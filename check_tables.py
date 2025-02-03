from sqlalchemy import create_engine, inspect
import sys

# Database URL (same as in your app settings)
DATABASE_URL = "sqlite:///./sql_app.db"

def check_database():
    try:
        # Create engine
        engine = create_engine(DATABASE_URL)
        inspector = inspect(engine)

        # Get all table names
        table_names = inspector.get_table_names()
        print("\nDatabase Tables:")
        print("-" * 50)
        
        if not table_names:
            print("No tables found in database!")
            return

        for table_name in table_names:
            print(f"\nTable: {table_name}")
            print("-" * 20)
            
            # Get columns for each table
            columns = inspector.get_columns(table_name)
            for column in columns:
                nullable = "NULL" if column['nullable'] else "NOT NULL"
                print(f"- {column['name']}: {column['type']} {nullable}")
            
            # Get foreign keys
            foreign_keys = inspector.get_foreign_keys(table_name)
            if foreign_keys:
                print("\nForeign Keys:")
                for fk in foreign_keys:
                    print(f"- {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")
            
            # Get indexes
            indexes = inspector.get_indexes(table_name)
            if indexes:
                print("\nIndexes:")
                for idx in indexes:
                    unique = "UNIQUE " if idx['unique'] else ""
                    print(f"- {unique}INDEX on {idx['column_names']}")

            print("\n" + "-" * 50)

if __name__ == "__main__":
    try:
        check_database()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    finally:
        sys.exit(0)