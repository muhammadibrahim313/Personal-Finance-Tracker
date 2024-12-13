import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os


class FinanceTrackerApp:
    def __init__(self):
        self.DATA_FILE = "transactions.json"
        self.load_data()
        st.set_page_config(page_title="Personal Finance Tracker", layout="wide")
        
    def load_data(self):
        if os.path.exists(self.DATA_FILE):
            with open(self.DATA_FILE, 'r') as file:
                self.transactions = json.load(file)
        else:
            self.transactions = []
            
    def save_data(self):
        with open(self.DATA_FILE, 'w') as file:
            json.dump(self.transactions, file)
            
    def _render_add_transaction(self):
        st.header("Add New Transaction")
        
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", datetime.now())
            amount = st.number_input("Amount", min_value=0.0, step=0.01)
            
        with col2:
            category = st.selectbox("Category", [
                "Income", "Housing", "Food", "Transportation", 
                "Utilities", "Entertainment", "Healthcare", "Other"
            ])
            description = st.text_input("Description")
            
        if st.button("Add Transaction"):
            if amount > 0 and description:
                transaction = {
                    "date": date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "category": category,
                    "description": description
                }
                self.transactions.append(transaction)
                self.save_data()
                st.success("Transaction added successfully!")
            else:
                st.error("Please fill in all fields correctly.")
                
    def _render_transaction_history(self):
        st.header("Transaction History")
        
        if not self.transactions:
            st.info("No transactions recorded yet.")
            return
            
        df = pd.DataFrame(self.transactions)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            categories = ['All'] + list(df['category'].unique())
            selected_category = st.selectbox("Filter by Category", categories)
        
        with col2:
            date_range = st.date_input(
                "Filter by Date Range",
                value=(df['date'].min(), df['date'].max()),
                key="date_range"
            )
            
        filtered_df = df.copy()
        if selected_category != 'All':
            filtered_df = filtered_df[filtered_df['category'] == selected_category]
            
        filtered_df = filtered_df[
            (filtered_df['date'].dt.date >= date_range[0]) &
            (filtered_df['date'].dt.date <= date_range[1])
        ]
        
        st.dataframe(
            filtered_df[['date', 'category', 'description', 'amount']],
            hide_index=True
        )
        
    def _render_financial_insights(self):
        st.header("Financial Insights")
        
        if not self.transactions:
            st.info("No transactions available for analysis.")
            return
            
        df = pd.DataFrame(self.transactions)
        df['date'] = pd.to_datetime(df['date'])
        
        # Summary statistics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_income = df[df['category'] == 'Income']['amount'].sum()
            st.metric("Total Income", f"${total_income:,.2f}")
            
        with col2:
            total_expenses = df[df['category'] != 'Income']['amount'].sum()
            st.metric("Total Expenses", f"${total_expenses:,.2f}")
            
        with col3:
            net_savings = total_income - total_expenses
            st.metric("Net Savings", f"${net_savings:,.2f}")
            
        # Spending by category
        expenses_by_category = df[df['category'] != 'Income'].groupby('category')['amount'].sum()
        fig = px.pie(
            values=expenses_by_category.values,
            names=expenses_by_category.index,
            title="Expenses by Category"
        )
        st.plotly_chart(fig)
        
        # Monthly trend
        monthly_expenses = df.set_index('date').resample('M')['amount'].sum()
        fig = px.line(
            x=monthly_expenses.index,
            y=monthly_expenses.values,
            title="Monthly Spending Trend"
        )
        st.plotly_chart(fig)
        
    def _render_budget_goals(self):
        st.header("Budget Goals")
        
        # Load or initialize budget goals
        if 'budget_goals' not in st.session_state:
            st.session_state.budget_goals = {
                "Housing": 1000,
                "Food": 500,
                "Transportation": 200,
                "Utilities": 300,
                "Entertainment": 200,
                "Healthcare": 300,
                "Other": 200
            }
            
        # Edit budget goals
        st.subheader("Set Monthly Budget Goals")
        
        updated_goals = {}
        cols = st.columns(3)
        for i, (category, amount) in enumerate(st.session_state.budget_goals.items()):
            with cols[i % 3]:
                updated_goals[category] = st.number_input(
                    f"{category} Budget",
                    min_value=0.0,
                    value=float(amount),
                    step=50.0,
                    key=f"budget_{category}"
                )
                
        if st.button("Update Budget Goals"):
            st.session_state.budget_goals = updated_goals
            st.success("Budget goals updated successfully!")
            
        # Compare actual spending with budget
        if self.transactions:
            st.subheader("Budget vs. Actual Spending")
            
            df = pd.DataFrame(self.transactions)
            current_month = datetime.now().strftime("%Y-%m")
            df['date'] = pd.to_datetime(df['date'])
            monthly_df = df[df['date'].dt.strftime("%Y-%m") == current_month]
            
            actual_spending = monthly_df[monthly_df['category'] != 'Income'].groupby('category')['amount'].sum()
            
            comparison_data = []
            for category, budget in st.session_state.budget_goals.items():
                actual = actual_spending.get(category, 0)
                comparison_data.append({
                    "Category": category,
                    "Budget": budget,
                    "Actual": actual,
                    "Remaining": budget - actual
                })
                
            comparison_df = pd.DataFrame(comparison_data)
            st.dataframe(comparison_df, hide_index=True)
            
    def run(self):
        st.title("Personal Finance Tracker")
        
        menu = ["Add Transaction", "Transaction History", "Financial Insights", "Budget Goals"]
        choice = st.sidebar.selectbox("Menu", menu)
        
        if choice == "Add Transaction":
            self._render_add_transaction()
        elif choice == "Transaction History":
            self._render_transaction_history()
        elif choice == "Financial Insights":
            self._render_financial_insights()
        elif choice == "Budget Goals":
            self._render_budget_goals()

def main():
    app = FinanceTrackerApp()
    app.run()

if __name__ == "__main__":
    main()