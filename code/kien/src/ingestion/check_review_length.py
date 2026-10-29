import pandas as pd

csv_path = "../../data/processed/data_clean.csv"
df = pd.read_csv(csv_path)

# In ra danh sách tên các cột có trong file CSV để kiểm tra
print("Danh sách các cột trong file:")
print(df.columns.tolist())

# In thử 2 dòng đầu tiên của file
print("\nDữ liệu mẫu:")
print(df.head(2))