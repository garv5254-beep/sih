import pandas as pd
import numpy as np
from datetime import timedelta
from sklearn.ensemble import HistGradientBoostingRegressor
import traceback

class InventoryML:
    def __init__(self):
        self.model = HistGradientBoostingRegressor(random_state=42)
        self.is_trained = False
        self.diagnostics = {}

    def engineer_features(self, df):
        # Ensure df is sorted by date
        df = df.sort_values(['product_id', 'date'])
        
        # Lag features (use shift to prevent leakage!)
        for lag in [1, 7, 14, 30]:
            df[f'lag_{lag}'] = df.groupby('product_id')['Daily_Quantity'].shift(lag)
            
        # Rolling features (must use shift(1) to prevent leakage)
        for window in [7, 14, 30]:
            df[f'rolling_mean_{window}'] = df.groupby('product_id')['Daily_Quantity'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).mean()
            )
            
        for window in [7, 30]:
            df[f'rolling_std_{window}'] = df.groupby('product_id')['Daily_Quantity'].transform(
                lambda x: x.shift(1).rolling(window, min_periods=1).std()
            )
            
        # Time features
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.dayofweek
        df['week_of_year'] = df['date'].dt.isocalendar().week
        df['month'] = df['date'].dt.month
        
        # Target: Today's quantity (since we shifted all features by 1)
        # So we predict 'Daily_Quantity' using previous days' data
        df['future_quantity_demand'] = df['Daily_Quantity']
        
        return df

    def prepare_data(self, sales_df, inventory_df):
        inv_skus = set(inventory_df['product_id'].unique()) if 'product_id' in inventory_df.columns else set()
        sales_skus = set()
        
        if not sales_df.empty:
            sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
            sales_df['quantity'] = pd.to_numeric(sales_df['quantity'], errors='coerce').fillna(0)
            
            # Remove invalid dates
            sales_df = sales_df.dropna(subset=['date', 'product_id'])
            
            sales_skus = set(sales_df['product_id'].unique())
            daily_sales = sales_df.groupby(['date', 'product_id'])['quantity'].sum().reset_index()
            daily_sales.rename(columns={'quantity': 'Daily_Quantity'}, inplace=True)
            
            min_date = daily_sales['date'].min()
            max_date = daily_sales['date'].max()
        else:
            daily_sales = pd.DataFrame(columns=['date', 'product_id', 'Daily_Quantity'])
            min_date = pd.Timestamp.today() - timedelta(days=90)
            max_date = pd.Timestamp.today()
            
        self.diagnostics['unique_inv_skus'] = len(inv_skus)
        self.diagnostics['unique_sales_skus'] = len(sales_skus)
        self.diagnostics['matched_skus'] = list(inv_skus.intersection(sales_skus))
        self.diagnostics['unmatched_sales_skus'] = list(sales_skus - inv_skus)
        self.diagnostics['inv_skus_without_sales'] = list(inv_skus - sales_skus)
        self.diagnostics['date_range'] = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
        
        # Create a full date range for EVERY inventory SKU to prevent ML leakage on zero-sale days
        all_dates = pd.date_range(start=min_date, end=max_date)
        
        if inv_skus:
            all_products = list(inv_skus)
            idx = pd.MultiIndex.from_product([all_dates, all_products], names=['date', 'product_id'])
            full_df = pd.DataFrame(index=idx).reset_index()
            
            df = pd.merge(full_df, daily_sales, on=['date', 'product_id'], how='left').fillna({'Daily_Quantity': 0})
        else:
            df = pd.DataFrame(columns=['date', 'product_id', 'Daily_Quantity'])
            
        # Merge with inventory for lead time (static features)
        if 'lead_time_days' in inventory_df.columns:
            inv_features = inventory_df[['product_id', 'lead_time_days']]
            df = pd.merge(df, inv_features, on='product_id', how='left')
            df['lead_time_days'] = pd.to_numeric(df['lead_time_days'], errors='coerce').fillna(5)
        else:
            df['lead_time_days'] = 5
            
        if not df.empty:
            df = self.engineer_features(df)
            
        return df

    def train(self, df):
        if df.empty:
            self.is_trained = False
            self.diagnostics['training_rows'] = 0
            self.diagnostics['model_status'] = "Failed - No Data"
            return
            
        # Drop rows with NaN target or lag_1 (the first day of the series)
        train_df = df.dropna(subset=['future_quantity_demand', 'lag_1']).copy()
        
        features = [
            'lag_1', 'lag_7', 'lag_14', 'lag_30',
            'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
            'rolling_std_7', 'rolling_std_30',
            'day_of_week', 'week_of_year', 'month',
            'lead_time_days'
        ]
        
        self.diagnostics['training_rows'] = len(train_df)
        
        if len(train_df) > 50:
            X = train_df[features].fillna(0)
            y = train_df['future_quantity_demand']
            try:
                self.model.fit(X, y)
                self.is_trained = True
                self.diagnostics['model_status'] = "Trained successfully"
            except Exception as e:
                self.is_trained = False
                self.diagnostics['model_status'] = f"Training Failed: {e}"
        else:
            self.is_trained = False
            self.diagnostics['model_status'] = "Insufficient Data (< 50 rows)"

    def predict_demand(self, sales_df, inventory_df):
        """
        Returns predictions and diagnostics.
        """
        self.diagnostics['fallback_skus'] = []
        
        if inventory_df.empty:
            return {}, self.diagnostics
            
        df = self.prepare_data(sales_df, inventory_df)
        
        if not self.is_trained:
            self.train(df)
            
        if df.empty:
            return {}, self.diagnostics
            
        # To predict today's demand, we take the LATEST actual date, 
        # and since we shifted features by 1, evaluating the model ON the latest date
        # gives us the prediction for the "next" logical day based on lags.
        latest_data = df.sort_values('date').groupby('product_id').last().reset_index()
        
        features = [
            'lag_1', 'lag_7', 'lag_14', 'lag_30',
            'rolling_mean_7', 'rolling_mean_14', 'rolling_mean_30',
            'rolling_std_7', 'rolling_std_30',
            'day_of_week', 'week_of_year', 'month',
            'lead_time_days'
        ]
        
        predictions = {}
        for _, row in latest_data.iterrows():
            pid = row['product_id']
            if self.is_trained:
                X_pred = (
                    row[features]
                    .infer_objects(copy=False)
                    .fillna(0)
                    .to_frame()
                    .T
                )
                try:
                    pred = self.model.predict(X_pred)[0]
                    pred = max(0.0, float(pred)) # Demand can't be negative
                except:
                    pred = max(0.0, float(row.get('rolling_mean_7', 0.0)))
                    self.diagnostics['fallback_skus'].append(pid)
            else:
                # Fallback to 7-day rolling average
                pred = max(0.0, float(row.get('rolling_mean_7', 0.0)))
                self.diagnostics['fallback_skus'].append(pid)
            
            predictions[pid] = pred
            
        return predictions, self.diagnostics

def generate_inventory_recommendations(inventory_df, sales_df, predictions, diagnostics):
    """
    Combines predictions with inventory data to generate robust reorder recommendations.
    """
    recs = []
    
    # Pre-calculate sales aggregates
    sales_30d = {}
    if not sales_df.empty:
        sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
        max_date = sales_df['date'].max()
        thirty_days_ago = max_date - timedelta(days=30)
        recent_sales = sales_df[sales_df['date'] >= thirty_days_ago]
        sales_30d = recent_sales.groupby('product_id')['quantity'].sum().to_dict()
        
    for _, row in inventory_df.iterrows():
        pid = row.get('product_id')
        name = row.get('Display_Product', row.get('product_name', 'Unknown Item'))
        
        # Clean numeric fields safely
        current_stock = max(0.0, float(pd.to_numeric(row.get('current_stock', 0), errors='coerce')))
        lead_time = max(1.0, float(pd.to_numeric(row.get('lead_time_days', 5), errors='coerce')))
        max_stock = max(1.0, float(pd.to_numeric(row.get('maximum_stock', 100), errors='coerce')))
        
        predicted_daily = float(predictions.get(pid, 0.0))
        sales_last_30 = float(sales_30d.get(pid, 0.0))
        
        # Inventory Calculations
        lead_time_demand = predicted_daily * lead_time
        
        # Safety Stock = max(0, std * sqrt(lead_time))
        # We approximate std dynamically based on prediction or sales variance.
        demand_std = predicted_daily * 0.4 # Proxy for std if unavailable
        safety_stock = max(0.0, demand_std * np.sqrt(lead_time))
        
        reorder_point = lead_time_demand + safety_stock
        
        if predicted_daily > 0:
            days_remaining = current_stock / predicted_daily
        else:
            days_remaining = 999.0
            
        # Reorder Recommendation
        if current_stock <= reorder_point:
            order_qty = max(0.0, max_stock - current_stock - lead_time_demand)
            order_qty = float(int(round(order_qty / 5) * 5))
            if order_qty == 0: order_qty = float(max_stock)
        else:
            order_qty = 0.0
            
        # Inventory Status
        if days_remaining <= lead_time and predicted_daily > 0:
            status = "CRITICAL"
        elif current_stock <= reorder_point:
            status = "LOW STOCK"
        elif predicted_daily > 0 and current_stock > reorder_point:
            status = "HEALTHY"
        elif sales_last_30 > 0:
            status = "SLOW MOVING"
        else:
            status = "DEAD STOCK"
            
        # Demand Classification
        if predicted_daily > 5:
            classification = "FAST MOVING"
        elif predicted_daily > 1:
            classification = "MEDIUM MOVING"
        elif sales_last_30 > 0:
            classification = "SLOW MOVING"
        else:
            classification = "DEAD STOCK"
            
        # AI Recommendation Text
        if pid in diagnostics.get('fallback_skus', []):
            fallback_msg = f"ML forecast unavailable for {pid} due to insufficient history. Using 7-day moving average fallback. "
        else:
            fallback_msg = ""
            
        if status in ["CRITICAL", "LOW STOCK"]:
            rec_text = f"{fallback_msg}Demand is approximately {predicted_daily:.1f} units/day and current inventory is approaching the reorder point. Consider ordering {int(order_qty)} units based on predicted demand and supplier lead time."
        elif status == "HEALTHY":
            rec_text = f"{fallback_msg}Stock levels are sufficient to cover expected demand. No immediate reorder is required."
        elif status == "SLOW MOVING":
            rec_text = f"{fallback_msg}Demand is slow. Monitor inventory closely before reordering."
        else:
            rec_text = f"{fallback_msg}No meaningful sales recently. Do not reorder."
            
        recs.append({
            'product_id': pid,
            'product_name': name,
            'current_stock': int(current_stock),
            'Sales_30_Days': int(sales_last_30),
            'Avg_Daily_Demand': round(sales_last_30 / 30.0, 2) if sales_last_30 > 0 else 0.0,
            'Predicted_Daily_Demand': round(predicted_daily, 2),
            'Days_Remaining': round(days_remaining, 1),
            'Reorder_Point': int(reorder_point),
            'Recommended_Order': int(order_qty),
            'status': status,
            'Classification': classification,
            'Recommendation': rec_text
        })
        
    return pd.DataFrame(recs)
