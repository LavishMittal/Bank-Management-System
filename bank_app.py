import json
import random
import string
from pathlib import Path
from typing import Optional

import streamlit as st

DATA_FILE = Path("data.json")


class Bank:
    def __init__(self, database: Path = DATA_FILE):
        self.database = database
        self.info = self._load_data()

    def _load_data(self):
        try:
            if self.database.exists():
                with open(self.database, "r", encoding="utf-8") as fs:
                    data = json.load(fs)
                    return data if isinstance(data, list) else []
            return []
        except Exception:
            return []

    def _update(self):
        with open(self.database, "w", encoding="utf-8") as fs:
            json.dump(self.info, fs, indent=4)

    @staticmethod
    def _account_number(existing_accounts=None):
        existing_accounts = existing_accounts or []
        existing_numbers = {acc["account_number"] for acc in existing_accounts}
        while True:
            alpha = random.choices(string.ascii_uppercase, k=3)
            num = random.choices(string.digits, k=4)
            acc_id = alpha + num
            random.shuffle(acc_id)
            account_number = "".join(acc_id)
            if account_number not in existing_numbers:
                return account_number

    def _find_user(self, account_number: str, pin: str) -> Optional[dict]:
        return next(
            (
                user
                for user in self.info
                if user["account_number"] == account_number and str(user["pin"]) == str(pin)
            ),
            None,
        )

    def create_account(self, name, age, email, pin):
        if age < 18:
            return False, "You must be at least 18 years old to create an account."
        if len(str(pin)) != 4 or not str(pin).isdigit():
            return False, "PIN must be exactly 4 digits."
        if any(user["email"].lower() == email.lower() for user in self.info):
            return False, "An account with this email already exists."

        account = {
            "name": name.strip(),
            "age": age,
            "email": email.strip(),
            "pin": str(pin),
            "account_number": self._account_number(self.info),
            "balance": 0,
        }
        self.info.append(account)
        self._update()
        return True, account

    def deposit_money(self, account_number, pin, amount):
        user = self._find_user(account_number, pin)
        if not user:
            return False, "Invalid account number or PIN."
        if amount <= 0 or amount > 10000:
            return False, "Deposit amount must be between 1 and 10000."
        user["balance"] += amount
        self._update()
        return True, user["balance"]

    def withdraw_money(self, account_number, pin, amount):
        user = self._find_user(account_number, pin)
        if not user:
            return False, "Invalid account number or PIN."
        if amount <= 0 or amount > 10000:
            return False, "Withdrawal amount must be between 1 and 10000."
        if user["balance"] < amount:
            return False, "Insufficient balance."
        user["balance"] -= amount
        self._update()
        return True, user["balance"]

    def account_details(self, account_number, pin):
        user = self._find_user(account_number, pin)
        if not user:
            return False, "Invalid account number or PIN."
        return True, {k: v for k, v in user.items() if k != "pin"}

    def update_details(self, account_number, pin, field, value):
        user = self._find_user(account_number, pin)
        if not user:
            return False, "Invalid account number or PIN."

        if field == "name":
            user["name"] = value.strip()
        elif field == "email":
            if any(acc["email"].lower() == value.lower() and acc != user for acc in self.info):
                return False, "Another account already uses this email."
            user["email"] = value.strip()
        elif field == "pin":
            if len(str(value)) != 4 or not str(value).isdigit():
                return False, "PIN must be exactly 4 digits."
            user["pin"] = str(value)
        else:
            return False, "Invalid field selected."

        self._update()
        return True, f"{field.title()} updated successfully."

    def delete_account(self, account_number, pin):
        user = self._find_user(account_number, pin)
        if not user:
            return False, "Invalid account number or PIN."
        self.info.remove(user)
        self._update()
        return True, "Account deleted successfully."


st.set_page_config(page_title="Simple Bank App", page_icon="🏦", layout="centered")
st.title("🏦 Simple Bank Management App")
st.caption("Create accounts, deposit, withdraw, view details, update information, and delete accounts.")

bank = Bank()
menu = st.sidebar.radio(
    "Choose an action",
    [
        "Create Account",
        "Deposit Money",
        "Withdraw Money",
        "Account Details",
        "Update Details",
        "Delete Account",
    ],
)


def auth_fields():
    account_number = st.text_input("Account Number")
    pin = st.text_input("4-digit PIN", type="password", max_chars=4)
    return account_number, pin


if menu == "Create Account":
    st.subheader("Open a new account")
    with st.form("create_account_form"):
        name = st.text_input("Full Name")
        age = st.number_input("Age", min_value=0, max_value=120, step=1)
        email = st.text_input("Email")
        pin = st.text_input("Create 4-digit PIN", type="password", max_chars=4)
        submitted = st.form_submit_button("Create Account")

    if submitted:
        ok, result = bank.create_account(name, int(age), email, pin)
        if ok:
            st.success("Account created successfully.")
            st.info(f"Your account number is: {result['account_number']}")
            st.json({k: v for k, v in result.items() if k != 'pin'})
        else:
            st.error(result)

elif menu == "Deposit Money":
    st.subheader("Deposit funds")
    with st.form("deposit_form"):
        account_number, pin = auth_fields()
        amount = st.number_input("Amount", min_value=1, max_value=10000, step=1)
        submitted = st.form_submit_button("Deposit")

    if submitted:
        ok, result = bank.deposit_money(account_number, pin, int(amount))
        if ok:
            st.success(f"Deposit successful. New balance: {result}")
        else:
            st.error(result)

elif menu == "Withdraw Money":
    st.subheader("Withdraw funds")
    with st.form("withdraw_form"):
        account_number, pin = auth_fields()
        amount = st.number_input("Amount", min_value=1, max_value=10000, step=1, key="withdraw_amount")
        submitted = st.form_submit_button("Withdraw")

    if submitted:
        ok, result = bank.withdraw_money(account_number, pin, int(amount))
        if ok:
            st.success(f"Withdrawal successful. Remaining balance: {result}")
        else:
            st.error(result)

elif menu == "Account Details":
    st.subheader("View account details")
    with st.form("details_form"):
        account_number, pin = auth_fields()
        submitted = st.form_submit_button("Show Details")

    if submitted:
        ok, result = bank.account_details(account_number, pin)
        if ok:
            st.json(result)
        else:
            st.error(result)

elif menu == "Update Details":
    st.subheader("Update account information")
    with st.form("update_form"):
        account_number, pin = auth_fields()
        field = st.selectbox("Field to update", ["name", "email", "pin"])
        value = st.text_input("New value")
        submitted = st.form_submit_button("Update")

    if submitted:
        ok, result = bank.update_details(account_number, pin, field, value)
        if ok:
            st.success(result)
        else:
            st.error(result)

elif menu == "Delete Account":
    st.subheader("Delete account")
    st.warning("This action is permanent.")
    with st.form("delete_form"):
        account_number, pin = auth_fields()
        confirm = st.checkbox("I understand this will permanently delete my account")
        submitted = st.form_submit_button("Delete Account")

    if submitted:
        if not confirm:
            st.error("Please confirm account deletion.")
        else:
            ok, result = bank.delete_account(account_number, pin)
            if ok:
                st.success(result)
            else:
                st.error(result)

