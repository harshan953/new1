import streamlit as st
import pandas as pd
from datetime import date
import os
import calendar

# File paths
EMPLOYEE_FILE = "data/employees.csv"
ATTENDANCE_FILE = "data/attendance.csv"
ADVANCE_FILE = "data/advance_cash.csv"

st.set_page_config(page_title="InOffice", layout="wide")

if st.session_state.get("logout_triggered"):
    for key in ["authenticated", "role", "logout_triggered"]:
        st.session_state.pop(key, None)
    st.rerun()

os.makedirs("data", exist_ok=True)

def load_data():
    if not os.path.exists(EMPLOYEE_FILE):
        pd.DataFrame(columns=["ID", "Name", "Salary"]).to_csv(EMPLOYEE_FILE, index=False)
    if not os.path.exists(ATTENDANCE_FILE):
        pd.DataFrame(columns=["Date", "ID", "Name", "Status"]).to_csv(ATTENDANCE_FILE, index=False)
    if not os.path.exists(ADVANCE_FILE):
        pd.DataFrame(columns=["ID", "Month", "Advance", "Months", "Installment"]).to_csv(ADVANCE_FILE, index=False)

    employees = pd.read_csv(EMPLOYEE_FILE)
    attendance = pd.read_csv(ATTENDANCE_FILE)
    advances = pd.read_csv(ADVANCE_FILE)
    return employees, attendance, advances

def save_employees(df): df.to_csv(EMPLOYEE_FILE, index=False)
def save_attendance(df): df.to_csv(ATTENDANCE_FILE, index=False)
def save_advances(df): df.to_csv(ADVANCE_FILE, index=False)

#🔐Login 
def login():
    st.title("🔐 InOffice Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username == "admin" and password == "admin123":
            st.session_state.authenticated = True
            st.session_state.role = "admin"
            st.session_state.rerun_trigger = True
        elif username == "hr" and password == "hr123":
            st.session_state.authenticated = True
            st.session_state.role = "hr"
            st.session_state.rerun_trigger = True
        else:
            st.error("Incorrect UserID or Password")

employees, attendance, advances = load_data()

if not st.session_state.get("authenticated", False):
    login()
    if st.session_state.get("rerun_trigger"):
        st.session_state.pop("rerun_trigger")
        st.rerun()
    st.stop()
#Admin & hr login details
role = st.session_state.get("role", "")
if role == "admin":
    menu_options = [
        "👥 Employees", "📝 Attendance", "📊 Dashboard", "💰 Salary Report",
        "📄 Salary Slips", "🏦 Advance Cash", "📤 Export", "🚪 Logout"
    ]
elif role == "hr":
    menu_options = ["📝 Attendance", "🚪 Logout"]
else:
    menu_options = ["🚪 Logout"]

menu = st.sidebar.radio("Menu", menu_options)
#logout 
if menu == "🚪 Logout":
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.success("🔓 Logged out successfully.")
    st.rerun()

#employees
elif menu == "👥 Employees":
    st.subheader("Manage Employees")
    with st.form("add_emp"):
        c1, c2, c3 = st.columns(3)
        with c1:
            eid = st.text_input("ID", key="add_emp_id")
        with c2:
            name = st.text_input("Name", key="add_emp_name")
        with c3:
            salary = st.number_input("Salary", min_value=0.0, key="add_emp_salary")

        if st.form_submit_button("Add"):
            if eid not in employees["ID"].values:
                employees.loc[len(employees)] = [eid, name, salary]
                save_employees(employees)
                st.success("✅ Employee added successfully!")

                # Clear form inputs
                st.session_state.setdefault("add_emp_id", "")
                st.session_state.setdefault("add_emp_name", "")
                st.session_state.setdefault("add_emp_salary", 0.0)

            else:
                st.warning("⚠️ Employee ID already exists!")

    st.write("Employees")
    edited = st.data_editor(employees, use_container_width=True, num_rows="dynamic")
    if st.button("💾 Update"): 
        save_employees(edited)
        st.success("✅ Employee data updated successfully!")
    remove_list = st.multiselect("Remove Employees", employees["Name"])
    if st.button("🗑️ Delete"): 
        employees = employees[~employees["Name"].isin(remove_list)]
        save_employees(employees)
        st.success("🗑️ Selected employees removed successfully!")
#Attendance
elif menu == "📝 Attendance":
    st.subheader("📝 Mark Attendance")
    sel_date = st.date_input("Select Date", value=date.today())
    date_str = sel_date.strftime("%Y-%m-%d")

    already_marked = date_str in attendance["Date"].values

    if already_marked:
        st.info(f"✅ Attendance already marked for **{date_str}**.")
        force_edit = st.checkbox("✏️ Edit attendance for this date?")
    else:
        st.warning(f"⚠️ Attendance not marked yet for **{date_str}**.")
        force_edit = True  # Allow marking if it's not marked yet

    if force_edit:
        status_options = ["Present", "Absent", "Half Day", "Company Holiday", "Sunday"]
        temp = []

        for _, row in employees.iterrows():
            emp_id = row["ID"]
            name = row["Name"]

            st.markdown(f"**{name} ({emp_id})**")
            status = st.radio(
                label="",
                options=status_options,
                horizontal=True,
                key=f"{emp_id}_{date_str}"
            )

            temp.append({
                "Date": date_str,
                "ID": emp_id,
                "Name": name,
                "Status": status
            })

        if st.button("✅ Submit Attendance"):
            attendance = attendance[attendance["Date"] != date_str]
            attendance = pd.concat([attendance, pd.DataFrame(temp)], ignore_index=True)
            save_attendance(attendance)
            st.success(f"✅ Attendance saved for {date_str}.")
    else:
        st.warning("Submit disabled. Attendance is already marked. Enable 'Edit attendance' to make changes.")

#Dashboard
elif menu == "📊 Dashboard":
    st.subheader("📊 Attendance Dashboard")

    if attendance.empty:
        st.info("No attendance records available.")
    else:
        tab1, tab2 = st.tabs(["📊 Monthly Summary", "📅 Daily View"])

        # --- Monthly Summary ---
        with tab1:
            month = st.selectbox("Select Month", sorted(attendance["Date"].str[:7].unique(), reverse=True))
            monthly = attendance[attendance["Date"].str.startswith(month)]
            counts = monthly.groupby(["ID", "Status"]).size().unstack(fill_value=0)
            for s in ["Present", "Absent", "Half Day", "Company Holiday", "Sunday"]:
                if s not in counts.columns:
                    counts[s] = 0
            summary = employees.set_index("ID").join(counts).fillna(0)
            summary["Paid Absents"] = summary["Absent"].apply(lambda x: min(x, 2))
            summary["Unpaid Absents"] = summary["Absent"].apply(lambda x: max(0, x - 2))
            st.dataframe(summary.reset_index()[[
                "ID", "Name", "Present", "Absent", "Paid Absents", "Unpaid Absents", "Half Day", "Company Holiday", "Sunday"
            ]])

        # --- Daily View ---
with tab2:
    st.markdown("### 📅 Daily Attendance Records")

    # Month filter
    selected_month = st.selectbox("📅 Filter Month", sorted(attendance["Date"].str[:7].unique(), reverse=True), key="daily_month")

    # Two filters side-by-side
    col1, col2 = st.columns(2)

    with col1:
        name_options = ["All"] + sorted(attendance["Name"].unique())
        selected_name = st.selectbox("👤 Filter by Employee Name", name_options, key="daily_name")

    with col2:
        status_options = ["All"] + sorted(attendance["Status"].unique())
        selected_status = st.selectbox("📌 Filter by Status", status_options, key="daily_status")

    # Filter the data
    daily_att = attendance[attendance["Date"].str.startswith(selected_month)]

    if selected_name != "All":
        daily_att = daily_att[daily_att["Name"] == selected_name]

    if selected_status != "All":
        daily_att = daily_att[daily_att["Status"] == selected_status]

    # Sort and show
    daily_summary = daily_att.sort_values(by=["Date", "Name"])
    st.dataframe(daily_summary, use_container_width=True)


#Salary Report
elif menu == "💰 Salary Report":
    st.subheader("💰 Salary Report")
    if attendance.empty: st.info("No data.")
    else:
        month = st.selectbox("Month", sorted(attendance["Date"].str[:7].unique(), reverse=True), key="sal_month")
        monthly = attendance[attendance["Date"].str.startswith(month)]
        counts = monthly.groupby(["ID", "Status"]).size().unstack(fill_value=0)
        for s in ["Present", "Absent", "Half Day", "Company Holiday", "Sunday"]:
            if s not in counts.columns: counts[s] = 0
        merged = employees.set_index("ID").join(counts).fillna(0)
        y, m = map(int, month.split("-"))
        days = calendar.monthrange(y, m)[1]
        merged["Daily"] = merged["Salary"] / days
        merged["Paid Absents"] = merged["Absent"].apply(lambda x: min(x, 2))
        merged["Unpaid Absents"] = merged["Absent"].apply(lambda x: max(0, x - 2))
        merged["Earned"] = (
            merged["Daily"] * (
                merged["Present"] +
                0.5 * merged["Half Day"] +
                merged["Company Holiday"] +
                merged["Paid Absents"]
            )
        )
        advance_deduction = []
        for idx, row in merged.iterrows():
            adv = advances[(advances["ID"] == idx) & (advances["Month"] == month)]
            deduction = adv["Installment"].sum() if not adv.empty else 0
            advance_deduction.append(deduction)
        merged["Advance Deduction"] = advance_deduction
        merged["Final Salary"] = merged["Earned"] - merged["Advance Deduction"]
        st.dataframe(merged.reset_index()[[
            "ID", "Name", "Salary", "Daily", "Present", "Half Day", "Company Holiday", "Paid Absents",
            "Unpaid Absents", "Advance Deduction", "Final Salary"
        ]].round(2))
                    #Salary Slips
elif menu == "📄 Salary Slips":
    st.subheader("📄 Download Salary Slips")

    if attendance.empty:
        st.info("No attendance data available.")
    else:
        month_options = sorted(attendance["Date"].str[:7].unique(), reverse=True)
        selected_month = st.selectbox("Select Month", month_options)

        employee_names = sorted(employees["Name"].unique())
        selected_emp = st.selectbox("Select Employee", employee_names)

        emp_row = employees[employees["Name"] == selected_emp]
        if emp_row.empty:
            st.error("❌ No employee found with the selected name.")
            st.stop()
        else:
            emp_id = emp_row["ID"].values[0]
            salary = emp_row["Salary"].values[0]


        # Filter attendance for the employee & month
        emp_att = attendance[(attendance["Name"] == selected_emp) & (attendance["Date"].str.startswith(selected_month))]
        counts = emp_att["Status"].value_counts().to_dict()

        # Fill missing statuses
        for status in ["Present", "Absent", "Half Day", "Company Holiday", "Sunday"]:
            counts[status] = counts.get(status, 0)

        y, m = map(int, selected_month.split("-"))
        total_days = calendar.monthrange(y, m)[1]
        daily = salary / total_days
        paid_absent = min(counts["Absent"], 2)
        unpaid_absent = max(0, counts["Absent"] - 2)
        earned = daily * (counts["Present"] + 0.5 * counts["Half Day"] + counts["Company Holiday"] + paid_absent)

        # Advance deduction
        adv = advances[(advances["ID"] == emp_id) & (advances["Month"] == selected_month)]
        adv_deduction = adv["Installment"].sum() if not adv.empty else 0
        final_salary = earned - adv_deduction

        st.markdown(f"""
        ### 🧾 Salary Slip for {selected_emp} – {selected_month}
        - **Employee ID:** {emp_id}
        - **Base Salary:** ₹{salary:.2f}
        - **Total Days in Month:** {total_days}
        - **Present:** {counts["Present"]} days  
        - **Absent:** {counts["Absent"]} days (Paid: {paid_absent}, Unpaid: {unpaid_absent})  
        - **Half Day:** {counts["Half Day"]}  
        - **Company Holiday:** {counts["Company Holiday"]}  
        - **Sunday:** {counts["Sunday"]}  
        - **Advance Deduction:** ₹{adv_deduction:.2f}
        - **Final Salary:** ₹{final_salary:.2f}
        """)

        # Optionally add download as text file
        if st.button("📥 Download Salary Slip"):
            slip_text = f"""Salary Slip - {selected_emp} ({emp_id}) - {selected_month}

Base Salary: ₹{salary:.2f}
Days in Month: {total_days}
Present: {counts["Present"]}
Absent: {counts["Absent"]} (Paid: {paid_absent}, Unpaid: {unpaid_absent})
Half Day: {counts["Half Day"]}
Company Holiday: {counts["Company Holiday"]}
Sunday: {counts["Sunday"]}
Advance Deduction: ₹{adv_deduction:.2f}
Final Salary: ₹{final_salary:.2f}
"""
            st.download_button("⬇️ Download as TXT", slip_text, file_name=f"{selected_emp}_{selected_month}_salary_slip.txt")
#Advance Cash
elif menu == "🏦 Advance Cash":
    st.subheader("🏦 Manage Advance Cash")
    st.markdown("### ➕ Add Advance")
    col1, col2 = st.columns(2)

    with col1:
        selected_emp = st.selectbox("Select Employee", employees["Name"], key="adv_emp")
        emp_row = employees[employees["Name"] == selected_emp]
        if emp_row.empty:
            st.error("❌ No employee found with the selected name.")
            st.stop()
        else:
            emp_id = emp_row["ID"].values[0]

    with col2:
        month = st.selectbox("Month", pd.date_range(start="2023-01-01", end=date.today(), freq="MS").strftime("%Y-%m").tolist()[::-1], key="adv_month")

    advance = st.number_input("Advance Amount", min_value=0)
    months = st.number_input("Repay In Months", min_value=1)

    if st.button("➕ Assign Advance"):
        installment = round(advance / months, 2)
        for i in range(months):
            y, m = map(int, month.split("-"))
            pay_month = pd.to_datetime(f"{y}-{m}-01") + pd.DateOffset(months=i)
            m_str = pay_month.strftime("%Y-%m")
            advances.loc[len(advances)] = [emp_id, m_str, advance, months, installment]
        save_advances(advances)
        st.success("Advance recorded.")

    st.markdown("### 📋 Existing Advance Records")
    emp_filter = st.selectbox("Filter by Employee", ["All"] + sorted(employees["Name"].unique()), key="filter_emp")
    if emp_filter != "All":
        filtered_id = employees[employees["Name"] == emp_filter]["ID"].values[0]
        filtered_advances = advances[advances["ID"] == filtered_id].copy()
    else:
        filtered_advances = advances.copy()

    edited_adv = st.data_editor(
        filtered_advances.reset_index(drop=True),
        num_rows="dynamic",
        use_container_width=True,
        key="edit_advances",
        column_config={
            "ID": st.column_config.TextColumn(disabled=True),
            "Month": st.column_config.TextColumn(disabled=True)
        },
        hide_index=True
    )

    if st.button("💾 Save Changes"):
        advances = edited_adv.copy()
        save_advances(advances)
        st.success("Changes saved.")

    st.markdown("### 🗑️ Delete Advance Records")
    edited_with_check = edited_adv.copy()
    edited_with_check["Delete"] = st.checkbox("Enable selection to delete", key="enable_delete")
    delete_ids = st.multiselect("Select rows to delete by index", edited_adv.index.tolist(), key="delete_indices")

    if st.button("❌ Delete Selected"):
        advances = advances.drop(index=delete_ids).reset_index(drop=True)
        save_advances(advances)
        st.success("Selected records deleted.")
        #Export
elif menu == "📤 Export":
    st.subheader("📤 Export Data")
    export_type = st.radio("Export Type", ["Attendance", "Salary Report"])
    month_options = sorted(attendance["Date"].str[:7].unique())
    selected_month = st.selectbox("Select Month", month_options)
    employee_options = ["All"] + sorted(employees["Name"].unique())
    selected_employee = st.selectbox("Select Employee", employee_options)

    if export_type == "Attendance":
        filtered = attendance[attendance["Date"].str.startswith(selected_month)]
        if selected_employee != "All":
            filtered = filtered[filtered["Name"] == selected_employee]
        st.write(f"Exporting {selected_employee} attendance for {selected_month}")
        st.download_button("📥 Download Attendance CSV", filtered.to_csv(index=False), file_name=f"{selected_employee}_{selected_month}_attendance.csv", mime="text/csv")

    elif export_type == "Salary Report":
        monthly = attendance[attendance["Date"].str.startswith(selected_month)]
        status_counts = monthly.groupby(["Name", "Status"]).size().unstack(fill_value=0)
        for status in ["Present", "Absent", "Half Day", "Company Holiday", "Sunday"]:
            if status not in status_counts.columns:
                status_counts[status] = 0
        merged = pd.merge(employees, status_counts, left_on="Name", right_index=True, how="left").fillna(0)
        year, month_num = map(int, selected_month.split("-"))
        days_in_month = calendar.monthrange(year, month_num)[1]
        merged["Daily Salary"] = merged["Salary"] / days_in_month
        merged["Paid Absents"] = merged["Absent"].apply(lambda x: min(x, 2))
        merged["Unpaid Absents"] = merged["Absent"].apply(lambda x: max(0, x - 2))
        merged["Salary Earned"] = (
            merged["Daily Salary"] * (
                merged["Present"] +
                merged["Company Holiday"] +
                merged["Paid Absents"] +
                0.5 * merged["Half Day"]
            )
        ).round(2)

        salary_data = merged[[
            "ID", "Name", "Salary", "Present", "Absent", "Paid Absents",
            "Unpaid Absents", "Half Day", "Company Holiday", "Salary Earned"
        ]]

        if selected_employee != "All":
            salary_data = salary_data[salary_data["Name"] == selected_employee]

        st.write(f"Exporting salary report for {selected_employee} - {selected_month}")
        st.download_button("📥 Download Salary Report CSV", salary_data.to_csv(index=False), file_name=f"{selected_employee}_{selected_month}_salary_report.csv", mime="text/csv")
