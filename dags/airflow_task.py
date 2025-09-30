from airflow import DAG
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.operators.python import PythonOperator
from datetime import timedelta
import pandas as pd 
import matplotlib.pyplot as plt
from airflow.utils.dates import days_ago



PG_CONN_ID = 'postgres_conn'

default_args = {
    'owner' : 'kiwilytics',
    'retries': 1,
    'retry_delay': timedelta(minutes=2),
    'depends_on_past': False
}

# Task 1: Fetch sales data (including prices) from PostgreSql database
def fetch_order_data():
    hook = PostgresHook(postgres_conn_id=PG_CONN_ID)
    conn = hook.get_conn()

    query = """
        SELECT 
            o.orderdate::date as sale_date,
            od.productid,
            p.productname,
            od.quantity,
            p.price
        FROM orders o 
        JOIN order_details od on o.orderid = od.orderid
        JOIN products p on od.productid = p.productid 
    """
    df = pd.read_sql(query,conn)
    df.to_csv('/home/kiwilytics/daily-sales-revenue/data/daily_sales.csv',index= False)

# Task 2: Calculate total revenue per day
def process_daily_revenue():
    df = pd.read_csv('/home/kiwilytics/daily-sales-revenue/data/daily_sales.csv')
    df['total_revenue'] = df['quantity'] * df['price']

    daily_revenue = df.groupby('sale_date')["total_revenue"].sum().reset_index()
    daily_revenue.to_csv('/home/kiwilytics/daily-sales-revenue/data/daily_revenue.csv',index=False)

# Task 3: Plot daily revenue
def plot_daily_revenue():
    df = pd.read_csv('/home/kiwilytics/daily-sales-revenue/data/daily_revenue.csv')
    df['sale_date']=pd.to_datetime(df['sale_date'])

    plt.figure(figsize=(12,6))
    plt.plot(df['sale_date'],df['total_revenue'],marker='o', color='blue')
    plt.title("Daily sales revenue")
    plt.xlabel('Date')
    plt.ylabel('Total Revenue')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    image_path = '/home/kiwilytics/daily-sales-revenue/images/daily_revenue.png'
    plt.savefig(image_path)
    print(f'Revenue chart saved to {image_path}')

# Define The DAG
with DAG(
    dag_id = "daily_sales_revenue",
    default_args = default_args,
    start_date = days_ago(1),
    schedule_interval='@daily',
    catchup = False,
    description = 'Computer and visualize daily revenue using pandas and matplotlib in airflow'
 ) as dag:

    task1 = PythonOperator(
        task_id = 'fetch_order_data',
        python_callable=fetch_order_data
    )

    task2 = PythonOperator(
        task_id = 'process_daily_revenue',
        python_callable=process_daily_revenue
    )

    task3 = PythonOperator(
        task_id = 'plot_daily_revenue',
        python_callable=plot_daily_revenue
    )

task1 >> task2 >> task3


