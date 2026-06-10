/* Step 1: Set file location */
filename churnf "/home/u64379393/Churn_rate_analysis/telco-customer-churn-by-IBM.csv";

/* Step 2: Import CSV into SAS */
proc import datafile=churnf
    out=work.churn_raw
    dbms=csv
    replace;
    guessingrows=max;
    getnames=yes;
run;

/* Step 3: Check dataset structure */
proc contents data=work.churn_raw;
run;

/* Step 4: View first 10 records */
proc print data=work.churn_raw(obs=10);
run;

proc contents data=work.churn_raw;
run;
data work.churn_clean;
    set work.churn_raw;

    /* Remove leading/trailing spaces from character columns */
    customerID       = strip(customerID);
    gender           = strip(gender);
    Partner          = strip(Partner);
    Dependents       = strip(Dependents);
    PhoneService     = strip(PhoneService);
    MultipleLines    = strip(MultipleLines);
    InternetService  = strip(InternetService);
    OnlineSecurity   = strip(OnlineSecurity);
    OnlineBackup     = strip(OnlineBackup);
    DeviceProtection = strip(DeviceProtection);
    TechSupport      = strip(TechSupport);
    StreamingTV      = strip(StreamingTV);
    StreamingMovies  = strip(StreamingMovies);
    Contract         = strip(Contract);
    PaperlessBilling = strip(PaperlessBilling);
    PaymentMethod    = strip(PaymentMethod);
    Churn            = strip(Churn);
run;
proc sort data=work.churn_clean nodupkey out=work.churn_nodup;
    by customerID;
run;
proc sql;
    select count(*) as total_rows
    from work.churn_nodup;
quit;

proc freq data=work.churn_nodup;
    tables Churn;
run;

data work.churn_flagged;
    set work.churn_nodup;

    if Churn = "Yes" then churn_flag = 1;
    else if Churn = "No" then churn_flag = 0;
run;

proc freq data=work.churn_flagged;
    tables churn_flag;
run;
data work.churn_features;
    set work.churn_flagged;

    /* Key flags for churn risk */
    if Contract = "Month-to-month" then month_to_month_flag = 1;
    else month_to_month_flag = 0;

    if MonthlyCharges >= 70 then high_monthly_charge_flag = 1;
    else high_monthly_charge_flag = 0;

    if InternetService = "Fiber optic" then fiber_flag = 1;
    else fiber_flag = 0;

    if TechSupport = "No" then no_techsupport_flag = 1;
    else no_techsupport_flag = 0;

    if PaymentMethod = "Electronic check" then electronic_check_flag = 1;
    else electronic_check_flag = 0;

    if PaperlessBilling = "Yes" then paperless_flag = 1;
    else paperless_flag = 0;

    if tenure < 12 then low_tenure_flag = 1;
    else low_tenure_flag = 0;
run;
data work.churn_scored;
    set work.churn_features;

    risk_score = 0;
    length risk_band $15;

    if month_to_month_flag = 1 then risk_score + 20;
    if low_tenure_flag = 1 then risk_score + 15;
    if high_monthly_charge_flag = 1 then risk_score + 10;
    if fiber_flag = 1 then risk_score + 10;
    if no_techsupport_flag = 1 then risk_score + 10;
    if electronic_check_flag = 1 then risk_score + 10;
    if paperless_flag = 1 then risk_score + 5;

    if risk_score <= 20 then risk_band = "Low";
    else if risk_score <= 40 then risk_band = "Medium";
    else if risk_score <= 60 then risk_band = "High";
    else risk_band = "Very High";
run;
proc freq data=work.churn_scored;
    tables risk_band;
run;
proc freq data=work.churn_scored;
    tables risk_band*Churn / norow nocol nopercent;
run;
data work.high_risk_customers;
    set work.churn_scored;
    if risk_band in ("High", "Very High");
run;

proc print data=work.high_risk_customers(obs=20);
    var customerID tenure Contract MonthlyCharges PaymentMethod InternetService 
        TechSupport risk_score risk_band Churn;
run;
data work.high_risk_actions;
    set work.high_risk_customers;

    length priority $2 recommended_action $50;

    if risk_band = "Very High" and MonthlyCharges >= 70 then do;
        priority = "P1";
        recommended_action = "Immediate retention call + discount offer";
    end;
    else if risk_band = "Very High" then do;
        priority = "P1";
        recommended_action = "Immediate retention call";
    end;
    else if risk_band = "High" and tenure < 12 then do;
        priority = "P2";
        recommended_action = "Onboarding support follow-up";
    end;
    else if risk_band = "High" and TechSupport = "No" then do;
        priority = "P2";
        recommended_action = "Offer tech support assistance";
    end;
    else do;
        priority = "P3";
        recommended_action = "Monitor and send engagement message";
    end;
run;

proc print data=work.high_risk_actions(obs=20);
    var customerID tenure Contract MonthlyCharges TechSupport risk_score risk_band priority recommended_action Churn;
run;
proc sql;
    create table work.project_summary as
    select 
        count(*) as total_customers,
        sum(churn_flag) as churned_customers,
        calculated churned_customers / calculated total_customers * 100 as churn_rate format=8.2,
        sum(case when risk_band = "High" then 1 else 0 end) as high_risk_customers,
        sum(case when risk_band = "Very High" then 1 else 0 end) as very_high_risk_customers
    from work.churn_scored;
quit;

proc print data=work.project_summary;
run;

proc freq data=work.churn_scored;
    tables Contract*Churn / norow nocol nopercent;
run;
libname mydata "/home/u64379393/Churn_rate_analysis";

data mydata.churn_scored;
    set work.churn_scored;
run;

data mydata.high_risk_actions;
    set work.high_risk_actions;
run;

data mydata.project_summary;
    set work.project_summary;
run;

proc export data=mydata.high_risk_actions
    outfile="/home/u64379393/Churn_rate_analysis/high_risk_actions.xlsx"
    dbms=xlsx
    replace;
run;
proc export data=mydata.project_summary
    outfile="/home/u64379393/Churn_rate_analysis/project_summary.xlsx"
    dbms=xlsx
    replace;
run;
proc export data=mydata.churn_scored
    outfile="/home/u64379393/Churn_rate_analysis/churn_scored.xlsx"
    dbms=xlsx
    replace;
run;
proc sgplot data=work.churn_scored;
    vbar Churn;
    title "Customer Churn Distribution";
run;
proc sgplot data=work.churn_scored;
    vbar Contract / group=Churn groupdisplay=cluster;
    title "Churn by Contract Type";
run;
proc sgplot data=work.churn_scored;
    vbar risk_band;
    title "Customer Risk Band Distribution";
run;
proc sgplot data=work.churn_scored;
    vbar risk_band / group=Churn groupdisplay=cluster;
    title "Risk Band vs Actual Churn";
run;
proc sgplot data=work.churn_scored;
    vbox MonthlyCharges / category=Churn;
    title "Monthly Charges by Churn Status";
run;


