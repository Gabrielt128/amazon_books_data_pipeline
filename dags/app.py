
#dag - directed acyclic graph

#tasks : 1) fetch amazon data (extract) 2) clean data (transform) 3) create and store data in table on postgres (load)
#operators : Python Operator and PostgresOperator
#hooks - allows connection to postgres
#dependencies

from datetime import datetime, timedelta
from airflow import DAG
import requests
import pandas as pd
from bs4 import BeautifulSoup
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import time

#1) fetch amazon data (extract) 2) clean data (transform)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}

# session = requests.Session()
# session.headers.update(headers)

def get_amazon_data_books(num_books, ti):
    # Base URL of the Amazon search results for data science books
    base_url = f"https://www.amazon.com/s?k=data+engineering+books"

    books = []
    seen_titles = set()  # To keep track of seen titles

    page = 1

    while len(books) < num_books:
        print(f"now we are at page {page}")
        url = f"{base_url}&page={page}"
        
        # Send a request to the URL
        session = requests.Session()
        session.headers.update(headers)
        response = session.get(url, headers=headers)

        if response.status_code != 200:
            print(f"Failed to retrieve page {page}, status code: {response.status_code}")
            break

        # Check if the request was successful
        # Parse the content of the request with BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Find book containers (you may need to adjust the class names based on the actual HTML structure)
        book_containers = soup.find_all("div", {"class": "s-result-item"})
        
        # Loop through the book containers and extract data
        for book in book_containers:
            title_element = book.find("h2")
            if title_element:
                title_span = title_element.find("span")
                if title_span:
                    title = title_span.get_text(strip=True)
                else:
                    print("Title span not found, skipping...")
                    continue
            else:
                print("Title not found, skipping...")
                continue


            author_element = book.find("a", class_="a-size-base")
            author = author_element.get_text(strip=True) if author_element else "Unknown"

            price_whole = book.find("span", class_="a-price-whole")
            price_decimal = book.find("span", class_="a-price-fraction")
            if price_whole:
                price = price_whole.get_text(strip=True)
                if price_decimal:
                    price += price_decimal.get_text(strip=True)
            else:
                price = "N/A" 

            if title not in seen_titles:
                seen_titles.add(title)
                books.append({"Title": title, "Author": author, "Price": price})
            if len(books) >= num_books:
                break
        
        # Increment the page number for the next iteration
        page += 1
        time.sleep(2)

    # Convert the list of dictionaries into a DataFrame
    df = pd.DataFrame(books)
    print(df)
    ti.xcom_push(key='book_data', value=df.to_dict('records'))

#3) create and store data in table on postgres (load)
    
def insert_book_data_into_postgres(ti):
    book_data = ti.xcom_pull(key='book_data', task_ids='fetch_book_data')
    if not book_data:
        raise ValueError("No book data found")

    postgres_hook = PostgresHook(postgres_conn_id='amazon_books')
    postgres_hook.run("DELETE FROM books;")
    insert_query = """
    INSERT INTO books (title, authors, price)
    VALUES (%s, %s, %s)
    """
    for book in book_data:
        postgres_hook.run(insert_query, parameters=(book['Title'], book['Author'], book['Price']))


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 20),
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'fetch_and_store_amazon_books',
    default_args=default_args,
    catchup=False,
    description='A DAG to fetch book data from Amazon and store it in Postgres',
    schedule_interval=None,
) as dag:

    fetch_book_data_task = PythonOperator(
        task_id='fetch_book_data',
        python_callable=get_amazon_data_books,
        op_args=[100],  
    )

    create_table_task = PostgresOperator(
        task_id='create_table',
        postgres_conn_id='amazon_books',
        sql="""
        CREATE TABLE IF NOT EXISTS books (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT,
            price TEXT,
            rating TEXT
        );
        """,
    )

    insert_book_data_task = PythonOperator(
        task_id='insert_book_data',
        python_callable=insert_book_data_into_postgres,
    )


    fetch_book_data_task >> create_table_task >> insert_book_data_task
