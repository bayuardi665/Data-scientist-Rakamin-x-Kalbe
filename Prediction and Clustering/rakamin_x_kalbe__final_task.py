# -*- coding: utf-8 -*-
"""Rakamin X Kalbe_ Final Task.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1yc2tSQaw6HtPuN4EmeEdw3dGozmvoCb7
"""

import pandas as pd
import numpy as np
import seaborn as ans
import matplotlib.pyplot as plt
import statsmodels.api as sm

!pip install pmdarima
!pip install kneed
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn import preprocessing
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from pmdarima import auto_arima
from sklearn.preprocessing import MinMaxScaler
from kneed import DataGenerator, KneeLocator
from matplotlib.cm import ScalarMappable
from matplotlib.colors import Normalize

from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt
from statsmodels.tsa.arima.model import ARIMA
from pandas.plotting import autocorrelation_plot

import warnings
warnings.filterwarnings('ignore')

"""# *Membuka data yang akan digunakan *"""

df_customer = pd.read_csv(r'/content/Customer.csv',delimiter = ';')
df_product = pd.read_csv(r'/content/Product.csv',delimiter = ';')
df_store = pd.read_csv(r'/content/Store.csv',delimiter = ';')
df_transaction = pd.read_csv(r'/content/Transaction.csv',delimiter = ';')

"""# **Data Cleansing**
  Fungsi utama dari data cleansing adalah untuk membersihkan, memperbaiki, dan mempersiapkan data agar dapat digunakan dalam analisis dan pemodelan.

Berikut beberapa tujuan utama dari data cleansing
1.   Menghilangkan Noise
2.   Mengisi Data yang Hilang
3.   Standarisasi Data
4.   Validasi Data
5.   Mengubah tipe data
6.   Memeriksa konsistensi data
7.   Mengatasi data duplikat



"""

df_customer.head()

df_product.head()

df_store.head()

df_transaction.head()

# proses melakukan data cleansing
# data cleansing pada df_customer
df_customer['Income'] = df_customer['Income'].replace('[,]','.',regex=True).astype('float')

# data clensing pada df_store
df_store['Latitude'] = df_store['Latitude'].replace('[,]','.',regex=True).astype('float')
df_store['Longitude'] = df_store['Longitude'].replace('[,]','.',regex=True).astype('float')

# data cleansing pada df_transaction
df_transaction['Date']= pd.to_datetime(df_transaction['Date'])
df_customer.head()

df_transaction.head()

"""# **Gabungkan semua data**"""

df_merge = pd.merge(df_transaction,df_customer, on = ['CustomerID'])
df_merge = pd.merge(df_merge,df_product.drop(columns=['Price']),on=['ProductID'])
df_merge = pd.merge(df_merge,df_store,on=['StoreID'])
df_merge.head()

"""# **Membuat Model Mechine Learning (time series)**

Model Machine learning Time Series yang akan digunakan yaitu ARIMA (AutoRegressive Integrated Moving Average) adalah salah satu metode analisis statistik yang digunakan untuk memodelkan dan meramalkan data deret waktu. model ARIMA ynag digunakan model ARIMA (p, d, q), di mana:

1. p adalah orde autoregresif, yang mengindikasikan berapa banyak nilai sebelumnya yang akan digunakan dalam model AR.
2. d adalah orde diferensiasi, yang mengindikasikan berapa kali diferensiasi yang diperlukan untuk menjadikan deret waktu stasioner.
3. q adalah orde moving average, yang mengindikasikan berapa banyak nilai gangguan acak sebelumnya yang akan digunakan dalam model MA.

Proses membangun model ARIMA melibatkan pemilihan nilai-nilai p, d, dan q yang paling sesuai untuk data deret waktu tertentu, pelatihan model dengan data historis, dan kemudian menggunakan model tersebut untuk meramalkan nilai-nilai masa depan.
"""

#model regresi time series arima
df_regresi = df_merge.groupby('Date').agg({'Qty':'sum'}).reset_index()
df_regresi.head()

# plot time series dalam 1 tahun dari bulan ke bulan
fig, ax = plt.subplots(figsize=(9, 5))
ans.lineplot(x = 'Date', y = 'Qty', data= df_regresi)
plt.tight_layout()

train_data_index = df_regresi.set_index('Date')
regresi_decomposition = seasonal_decompose(train_data_index)

# plot decomposition
fig, (ax1, ax2, ax3, ax4) = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
regresi_decomposition.trend.plot(ax=ax1)
ax1.set_ylabel('Observed')

regresi_decomposition.trend.plot(ax=ax2)
ax2.set_ylabel('Trend')

regresi_decomposition.seasonal.plot(ax=ax3)
ax3.set_ylabel('Seasonal')

regresi_decomposition.resid.plot(ax=ax4)
ax4.set_ylabel('Residual')

plt.tight_layout()
plt.show()

"""# *Mengecek stasioner data menggunakan (Augmented Dickey-Fuller test) *
  Augmented Dickey-Fuller (ADF) test adalah sebuah tes statistik yang digunakan untuk menguji apakah suatu deret waktu stasioner atau tidak. Dalam konteks pengujian stasioneritas, konsep stasioneritas mengacu pada deret waktu yang statistikanya tetap atau tidak berubah sepanjang waktu. ADF test adalah salah satu alat penting dalam analisis deret waktu, terutama dalam pemodelan time series seperti ARIMA (AutoRegressive Integrated Moving Average).
"""

result = adfuller(df_regresi['Qty'])
print('ADF Statistic: %f' % result[0])
print('p-value: %f' % result[1])
print('Critical Values:')
for key, value in result[4].items():
  print('\t%s: %.3f' % (key, value))

    # Interpret the results
if result[1] <= 0.05:
  print("The data is stationary (reject the null hypothesis)")
else:
  print("The data is non-stationary (fail to reject the null hypothesis)")

"""**Mencari Nilai P dan Q untuk model ARIMA**"""

plt.rcParams.update({'figure.figsize':(9,7), 'figure.dpi':120})

# Original Series
fig, (ax1, ax2) = plt.subplots(2)
ax1.plot(df_regresi.Qty); ax1.set_title('Original Series'); ax1.axes.xaxis.set_visible(False)
# 1st Differencing
ax2.plot(df_regresi.Qty.diff(periods = 7)); ax2.set_title('7st Order Differencing'); ax2.axes.xaxis.set_visible(False)

plt.show()

"""# **Mencari nilai P menggunakan PACF dan Q menggunkan ACF**
ACF (Autocorrelation Function) dan PACF (Partial Autocorrelation Function)



*   Plot ACF: ACF adalah grafik fungsi korelasi antara nilai-nilai dalam deret waktu dengan nilai-nilai sebelumnya dalam deret waktu. Plot ACF dapat membantu mengidentifikasi orde autoregresif yang potensial. Dalam plot ACF, puncak-puncak yang melampaui area bayangan adalah indikasi dari orde autoregresif yang mungkin. Orde autoregresif adalah jumlah lag (nilai-nilai sebelumnya) yang signifikan dalam plot ACF.
*   Plot PACF: PACF adalah grafik fungsi korelasi parsial yang memeriksa hubungan antara dua titik dalam deret waktu dengan mengontrol semua lag yang berada di antara keduanya. Plot PACF membantu lebih mempersempit nilai p yang mungkin. Orde autoregresif yang signifikan dalam plot PACF adalah nilai p yang potensial.
*   Setelah melakukan plot ACF dan PACF,dapat mulai eksplorasi berbagai nilai p untuk membangun beberapa model ARIMA dengan orde yang berbeda. menggunakan alat statistik atau perangkat lunak seperti Python dengan paket seperti Statsmodels atau R untuk menghitung model ARIMA dengan nilai p yang berbeda dan membandingkannya.



"""

# menggunakan Data Original
plot_acf(df_regresi['Qty'].dropna(),lags=30)
plt.xlabel('lag')
plt.ylabel('Autocorrelation')
plt.title('Autocorellation Function(ACF)')
plt.show()
# plot PACF
plot_pacf(df_regresi['Qty'].dropna(),lags=30)
plt.xlabel('lag')
plt.ylabel('Partial Autocorrelation')
plt.title('Partial Autocorellation Function(PACF)')
plt.show()

# Menggunakn data yang sudah di Differencing
plot_acf(df_regresi.Qty.diff(periods = 7).dropna(),lags=30)
plt.xlabel('lag')
plt.ylabel('Autocorrelation')
plt.title('Autocorellation Function(ACF)')
plt.show()
# plot PACF
plot_pacf(df_regresi.Qty.diff(periods = 7).dropna(),lags=30)
plt.xlabel('lag')
plt.ylabel('Partial Autocorrelation')
plt.title('Partial Autocorellation Function(PACF)')
plt.show()

df_regresi.head

"""Menggunakn auto arima sebagai perbandingan untuk menentunkan nilai orde yang paling sesuai untuk digunakan dapat dilihat nilai orde yang digunakan yaitu (,0,0,0) (2,1,1,7) meruapakan nilai terbaik yang dapat digunakan."""

#Mencari nilai P,D,Q dengan menggunakna auto arima
model= auto_arima(df_regresi['Qty'],start_p=0, start_q=0,
                           max_p=0, max_q=0, m=7,
                           start_P=0, seasonal=True,
                           d=0, D=1, trace=True,
                           error_action='ignore',
                           suppress_warnings=True,
                           stepwise=True)

                  #seasonal= False, trace= True, allow_nan_inf=True)

"""Membagi data menjadi data_train dan data_test dengan perbandingan 80% data training dan 20% data test"""

cut_off = round(df_regresi.shape[0] * 0.8) # sebanyak 80% data akan digunakan sebagai data training dan 20% data akan digunakan sebagai data test
df_train = df_regresi[:cut_off]
df_test = df_regresi[cut_off:].reset_index(drop=True)

df_train

df_test.head()

#Plot data tarin dan data test
plt.figure(figsize=(20,5))
ans.lineplot(data=df_train, x=df_train['Date'],y=df_train['Qty'])
ans.lineplot(data=df_test, x=df_test['Date'],y=df_train['Qty'])

#calculasi RMSE dan MAE
def rmse (y_actual, y_pred):
  print(f'RMSE Value{mean_squared_error(y_actual, y_pred)** 0.5}')

# fungsi MAE
def eval(y_actual, y_pred):
  rmse(y_actual, y_pred)
  print(f'MAE Value{mean_absolute_error(y_actual, y_pred)** 0.5}')

# Fit ARIMA (0,0,0) seasonal (2,1,1)[7]
order = (0,0,0)
seasonal_order = (2,1,1,7)
model= sm.tsa.SARIMAX(df_train['Qty'],order = order, seasonal_order = seasonal_order)
fit_qty = model.fit()
print(fit_qty.summary())

from statsmodels.stats.diagnostic import acorr_ljungbox
mod = ARIMA(df_train['Qty'], order=order)
res = mod.fit()
jlung = acorr_ljungbox(res.resid)

# Prediksi model arima yang digunakan
# ARIMA (0,0,0) seasonal (2,1,1)[7]
df_train = df_train.set_index('Date')
df_test = df_test.set_index('Date')

y_pred = fit_qty.get_forecast(len(df_test))

y_pred_df = y_pred.conf_int()
y_pred_df['prediction'] = fit_qty.predict(start = y_pred_df.index[0],end = y_pred_df.index[-1])
y_pred_df.index = df_test.index
y_pred_out = y_pred_df['prediction']

eval(df_test['Qty'],y_pred_out)

plt.figure(figsize=(10,8))
plt.plot(df_train['Qty'])
plt.plot(df_test['Qty'],color = 'red')
plt.plot(y_pred_out, color = 'black', label = 'Arima Prediction')

plt.legend()
plt.tight_layout()

# Melakukan Forecast dari data yang digunakan selama satu bulan
forecast_length = 31
forecast_result = fit_qty.get_forecast(forecast_length)
forecast_result_arima = forecast_result.conf_int()
forecast_result_arima['forecasted Qty'] = fit_qty.predict(start = forecast_result_arima.index[0], end = forecast_result_arima.index[-1])
forecast_result_arima['Date'] = pd.date_range(start ='2023-01-01', end = '2023-01-31')
forecast_result_arima.set_index('Date', inplace = True)
forecast_result_arima.head()

plt.figure(figsize = (10,8))
plt.plot(df_train[ 'Qty'])
plt.plot(df_test[ 'Qty'], color = 'red')
plt.plot(y_pred_out, color = 'black', label = 'ARIMA Predictions')
plt.plot(forecast_result_arima['forecasted Qty'], color = 'green', label = 'ARIMA Forecasted')
plt.legend()
plt.tight_layout()

"""## **Clustering**

 K-Means adalah salah satu metode yang paling umum digunakan dalam analisis klaster atau clustering dalam ilmu data dan statistik. Tujuannya adalah untuk mengelompokkan data menjadi klaster atau kelompok berdasarkan kesamaan atribut atau karakteristik tertentu. Kluster-kluster ini dibentuk dengan cara meminimalkan variasi (varians) dalam setiap kluster dan memaksimalkan variasi antar kluster.
"""

df_merge.head()

#identifikasi kolom dengan korelasi yang tinggi/ repundan
df_merge.corr()

#melakukan clustering model
df_cluster = df_merge.groupby('CustomerID').agg({'TransactionID':
                                                 'count', 'Qty':'sum',
                                                 'TotalAmount':'sum'}).reset_index()
df_cluster.tail()

"""-> Normalisasi data dalam clustering K-Means adalah langkah penting dalam
persiapan data sebelum menerapkan algoritma K-Means. Normalisasi bertujuan untuk mengubah rentang nilai atribut atau fitur dalam data agar memiliki skala yang seragam, sehingga semua atribut memiliki pengaruh yang seimbang dalam proses clustering. Tanpa normalisasi, atribut dengan skala yang besar atau varian yang tinggi akan mendominasi dalam pembentukan kluster, yang dapat menghasilkan hasil yang bias. DIsini saya menggunakna Min-Max Scaling: Ini adalah salah satu metode normalisasi yang paling umum. Min-Max scaling mengubah setiap atribut sehingga nilainya berada dalam rentang [0, 1],
"""

#Normalisasi Data
df_normalis= df_cluster.drop('CustomerID',axis = 1)
normalis = df_normalis.columns

df_normalisasi = MinMaxScaler().fit_transform(df_normalis)
df_normalisasi = pd.DataFrame(data = df_normalisasi, columns=normalis)

df_normalisasi.head()

"""Elbow Method adalah salah satu teknik yang digunakan untuk memilih jumlah kluster yang optimal dalam algoritma clustering, seperti K-Means. Tujuannya adalah untuk menemukan jumlah kluster yang paling sesuai dengan struktur data yang ada.
langkah langkah elbow method
1. Pilih Rentang Jumlah Kluster: Langkah pertama adalah menentukan rentang jumlah kluster yang akan Anda coba. Anda biasanya memulai dengan jumlah kluster yang rendah, misalnya 2 kluster, dan meningkatkannya secara bertahap hingga jumlah kluster tertentu, yang mungkin mencakup sebagian besar data Anda.

2. Hitung Inertia (Within-Cluster Sum of Squares): Untuk setiap jumlah kluster dalam rentang yang Anda tentukan, jalankan algoritma clustering (misalnya, K-Means) dan hitung nilai inertia atau dalam-cluster sum of squares. Inertia adalah jumlah kuadrat jarak antara setiap data dalam kluster dengan pusat klusternya. Ini mengukur seberapa kompak kluster-kelompoknya. Nilai inertia lebih rendah menunjukkan bahwa data dalam kluster lebih erat terkumpul.

3. Plot Nilai Inertia: Buat grafik yang menunjukkan jumlah kluster pada sumbu X dan nilai inertia pada sumbu Y. Ini akan menghasilkan grafik yang menyerupai lengan manusia.

4. Identifikasi "Elbow": Lihat grafik nilai inertia. Pada awalnya, nilai inertia akan menurun seiring dengan peningkatan jumlah kluster. Namun, pada suatu titik, penurunan akan melambat, dan grafik akan membentuk kurva seperti siku (elbow). Titik ini disebut "elbow point."

5. Pilih Jumlah Kluster Optimal: Jumlah kluster optimal dipilih berdasarkan grafik elbow. Ini adalah jumlah kluster di mana penurunan nilai inertia tidak lagi signifikan atau lambat. Biasanya, jumlah kluster optimal adalah jumlah kluster yang terletak di sekitar siku grafik elbow. Ini adalah jumlah kluster yang mempertahankan keseimbangan antara kompaknya kluster (rendahnya inertia) dan jumlah kluster yang terlalu banyak.
"""

#Implementasi menggunakn elbow method
inersia_value = []
k_value = range(1, 11)

for k in k_value:
  kmeans = KMeans(n_clusters=k, random_state=0)
  kmeans.fit(df_normalisasi)
  inersia_value.append(kmeans.inertia_)

plt.style.use("fivethirtyeight")
plt.plot(range(1, 11), inersia_value)
plt.xticks(range(1, 11))
plt.title('Elbow Method for Optimal K')
plt.xlabel("Number of Clusters")
plt.ylabel("inersia value")
plt.show()

# Menentukan nilai K dengan elbow method secara otomatis
kl = KneeLocator(range(1, 11), inersia_value, curve="convex", direction="decreasing" )
kl.elbow

"""Silhouette Coefficient adalah metrik evaluasi yang digunakan untuk mengukur seberapa baik objek-objek dalam kluster telah dikelompokkan dengan baik dalam analisis clustering. Metrik ini membantu dalam menilai kualitas klustering dengan memberikan skor untuk setiap data point berdasarkan seberapa baik data tersebut dikelompokkan dengan anggota kluster lainnya dibandingkan dengan kluster lainnya.

Skor Silhouette Coefficient berkisar antara -1 hingga +1, dan hasil interpretasinya adalah sebagai berikut:

1. Nilai positif mendekati +1: Ini menunjukkan bahwa objek dalam kluster tersebut dikelompokkan dengan sangat baik, dengan sedikit atau tanpa tumpang tindih dengan kluster lainnya.

2. Nilai nol: Ini menunjukkan bahwa objek tersebut berada tepat pada batas antara dua kluster yang berdekatan atau memiliki kesulitan dalam menentukan kluster yang sesuai.

3. Nilai negatif mendekati -1: Ini menunjukkan bahwa objek tersebut mungkin ditempatkan dalam kluster yang salah dan lebih baik jika ditempatkan dalam kluster lain.

Keuntungan penggunaan Silhouette Coefficient adalah kemampuannya untuk memberikan informasi tentang seberapa baik klustering telah dilakukan tanpa memerlukan pengetahuan sebelumnya tentang label kelas sebenarnya (dalam metode unsupervised learning).
"""

# mencari nilai Silhouette Coefficient
silhouette_value = []
k_value = range(2, 11)

# Notice you start at 2 clusters for silhouette coefficient
for k in k_value:
  kmeans = KMeans(n_clusters=k, random_state=0)
  kmeans.fit(df_normalisasi)
  score = silhouette_score(df_normalisasi, kmeans.labels_)
  silhouette_value.append(score)

plt.style.use("fivethirtyeight")
plt.plot(range(2, 11), silhouette_value)
plt.xticks(range(2, 11))
plt.title('Silhouette Score for Optimal K')
plt.xlabel("Number of Clusters")
plt.ylabel("Silhouette Coefficient")
plt.show()

"""Clustering dengan menggunakna K=3 dan K= 7 kemudian diplih hasil yang paling bagus diantara keduanya"""

# Clustering dengan K = 3
kmeans = KMeans(n_clusters=3, random_state=0)
df_cluster['Cluster']= kmeans.fit_predict(df_cluster)
df_kmean3 = df_cluster
df_kmean3.head(10)

# Calculate the mean for each column grouped by 'Cluster'
cluster_means = df_kmean3.groupby('Cluster')[['TransactionID', 'Qty', 'TotalAmount']].mean()

# Display the calculated means
cluster_means.head()

"""Hasil jumlah, total, mean, median, dan std untuk masing masing cluster 0,1,2 dari TransaksiID, QTY dan Total Amount"""

# Group the data by 'Cluster' and calculate count, sum, mean, median, and standard deviation
cluster_summary = df_kmean3.groupby('Cluster')[['TransactionID', 'Qty', 'TotalAmount']].agg(
    {'TransactionID': ['count', 'sum', 'mean', 'median', 'std'],
     'Qty': ['count', 'sum', 'mean', 'median', 'std'],
     'TotalAmount': ['count', 'sum', 'mean', 'median', 'std']}
)

# Rename the columns for clarity
cluster_summary.columns = ['TransactionID_Count', 'TransactionID_Sum', 'TransactionID_Mean', 'TransactionID_Median', 'TransactionID_Std',
                            'Qty_Count', 'Qty_Sum', 'Qty_Mean', 'Qty_Median', 'Qty_Std',
                            'TotalAmount_Count', 'TotalAmount_Sum', 'TotalAmount_Mean', 'TotalAmount_Median', 'TotalAmount_Std']
cluster_summary.head()

#jumlah customer tiap cluster :
Customer_count3 = df_cluster['Cluster'].value_counts()
print('Jumlah customer tiap cluster adalah')
print(Customer_count3)

# Presentasi jumlah customer tiap clusternya.
percentage_customer_count = (Customer_count3 / Customer_count3.sum()) * 100

# Create a colormap based on the percentage values
cmap = plt.get_cmap('coolwarm')
normalize = Normalize(vmin=percentage_customer_count.min(), vmax=percentage_customer_count.max())
colors = [cmap(normalize(value)) for value in percentage_customer_count]

# Plot the percentages with colored bars
plt.figure(figsize=(8, 6))
bars = plt.bar(percentage_customer_count.index, percentage_customer_count, color=colors)
plt.xlabel('Cluster')
plt.ylabel('Percentage of Customers')
plt.title('Percentage of Customers in Each Cluster')
plt.xticks(rotation=0)  # Rotate x-axis labels if needed

# Add percentage labels on top of each bar
for bar, value in zip(bars, percentage_customer_count):
    plt.text(bar.get_x() + bar.get_width() / 2, value + 1, f'{value:.2f}%', ha='center', va='bottom', fontsize=10)

# Add color legend
sm = ScalarMappable(cmap=cmap, norm=normalize)
sm.set_array([])
cbar = plt.colorbar(sm, orientation='vertical')
cbar.set_label('Color by Percentage')

plt.tight_layout()
plt.show()

# memvisiluasikan data
plt.scatter(df_kmean3['TransactionID'],df_kmean3['Qty'],c = df_kmean3['Cluster'], cmap ='rainbow')
plt.xlabel('Total Transaction')
plt.ylabel('Total Qty')
plt.title('K-Mean Clustering K = 3')
plt.show()

#Cluster Kmean dengan K = 7
kmeans = KMeans(n_clusters=8, random_state=0)
df_cluster['Cluster']= kmeans.fit_predict(df_cluster)
df_kmean7 = df_cluster
df_kmean7.head(10)

#jumlah customer tiap cluster :
Customer_count = df_kmean7['Cluster'].value_counts()
print('Jumlah customer tiap cluster adalah')
print(Customer_count)

"""Hasil jumlah, total, mean, median, dan std untuk masing masing cluster 0,1,2 dari TransaksiID, QTY dan Total Amount"""

# Group the data by 'Cluster' and calculate count, sum, mean, median, and standard deviation
cluster_summary = df_kmean7.groupby('Cluster')[['TransactionID', 'Qty', 'TotalAmount']].agg(
    {'TransactionID': ['count', 'sum', 'mean', 'median', 'std'],
     'Qty': ['count', 'sum', 'mean', 'median', 'std'],
     'TotalAmount': ['count', 'sum', 'mean', 'median', 'std']}
)

# Rename the columns for clarity
cluster_summary.columns = ['TransactionID_Count', 'TransactionID_Sum', 'TransactionID_Mean', 'TransactionID_Median', 'TransactionID_Std',
                            'Qty_Count', 'Qty_Sum', 'Qty_Mean', 'Qty_Median', 'Qty_Std',
                            'TotalAmount_Count', 'TotalAmount_Sum', 'TotalAmount_Mean', 'TotalAmount_Median', 'TotalAmount_Std']
cluster_summary.head(8)

#Presentasi jumlah Customer tiap clusternya
percentage_customer_count = (Customer_count / Customer_count.sum()) * 100

# Create a colormap based on the percentage values
cmap = plt.get_cmap('coolwarm')
normalize = Normalize(vmin=percentage_customer_count.min(), vmax=percentage_customer_count.max())
colors = [cmap(normalize(value)) for value in percentage_customer_count]

# Plot the percentages with colored bars
plt.figure(figsize=(10, 6))
bars = plt.bar(percentage_customer_count.index, percentage_customer_count, color=colors)
plt.xlabel('Cluster')
plt.ylabel('Percentage of Customers')
plt.title('Percentage of Customers in Each Cluster')
plt.xticks(rotation=0)  # Rotate x-axis labels if needed

# Add percentage labels on top of each bar
for bar, value in zip(bars, percentage_customer_count):
    plt.text(bar.get_x() + bar.get_width() / 2, value + 1, f'{value:.2f}%', ha='center', va='bottom', fontsize=10)

# Add color legend
sm = ScalarMappable(cmap=cmap, norm=normalize)
sm.set_array([])
cbar = plt.colorbar(sm, orientation='vertical')
cbar.set_label('Color by Percentage')

plt.tight_layout()
plt.show()

# memvisiluasikan data
plt.scatter(df_kmean7['TransactionID'],df_kmean7['Qty'],c = df_kmean7['Cluster'], cmap ='rainbow')
plt.xlabel('Total Transaction')
plt.ylabel('Total Qty')
plt.title('K-Mean Clustering K = 7')
plt.show()

"""**Cluster Interpretasi**

Berdasarkan Cluster yang dipilih yaitu 3 dapat disimpulkan dan dikelompokkan berdasarkan Clusternya yaitu :

1. Cluster 0 -  Customer Legend
   Merupakan customer dengan tier menengah dengan total Customer sebanyak 90 Customer atau sekitar 20,13% dengan rata rata transaksi sebanyak 15 kali, sedangkan total kualitas produk yang di beli yaitu 58 produk dan rata rata jumlah uang yang di gunakan yaitu sekitar 548k dan total uang yang digunakan yaitu 49 juta
2. Cluster 1 - Customer Mytic
   Merupakan customer dengan tier tertinggi dengan total Customer sebanyak 186 Customer atau sekitar 41,61% dengan rata rata transaksi sebanyak 11 kali, sedangkan total kualitas produk yang di beli yaitu 42 produk dan rata rata jumlah uang yang di gunakan yaitu sekitar 348k dan total uang yang digunakan yaitu 71 juta
3. Cluster 2 - Customer Epic
	 Merupakan customer dengan tier bawah dengan total Customer sebanyak 171 Customer atau sekitar 38,26% dengan rata rata transaksi sebanyak 8 kali, sedangkan total kualitas produk yang di beli yaitu 29 produk dan rata rata jumlah uang yang di gunakan yaitu sekitar 241k dan total uang yang digunakan yaitu 41 juta.

 ** Business Recommendation**

1. Customer Epic 	: Memberikan promo atau diskon pada saat awal melakukan belanja agar terkesan serta memberikan pelayana yang baik. Apabila customer jarang melakukan transaksi bisa mengirimkan email atau sebuah pemberitahuan mengenai promo promo yang sedang berlangsung serta memberi ucapan atau caption yang menarik agar pembeli kembali untuk membeli barang.  

2. Customer Legend 	: Pada tier ini customer bisa menjadi customer Mytic ataupun customer Epic. Dengan memberikan diskon atau penawaran ekslusif dengan waktu terbatas agar customer dapat berberlanja lebih sering serta memberikan poin atau reward yang dapat di tukarkan menjadi sebuah diskon tambahan atau dapat disimpan. Mengirimkan notifikasi tentang penawaran produk terkini dan memberikan ucapan untuk menarik membeli barang.

3. Customer Mytic 	: Merupakan tier paling tinggi dengan berbagai keuntungan seperti mendapat diskon yang lebih beragam dari tier yang lain, memiliki penawaran khusus, serta memberikan point yang dapat dikumpulkan atau di tukar serta akses untuk produk produk terbaru yang belum di luncurkan dan ekslusif memberikan pelayanan yang sangat baik baik dari ruangan atau dari pelayannya.


"""