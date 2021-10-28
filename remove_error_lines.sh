mkdir wrong; 
mv data/yellow_tripdata_2010-02.csv data/yellow_tripdata_2010-03.csv wrong/; 
sed -E '/(.*,){18,}/d' wrong/yellow_tripdata_2010-02.csv > data/yellow_tripdata_2010-02.csv; 
sed -E '/(.*,){18,}/d' wrong/yellow_tripdata_2010-03.csv > data/yellow_tripdata_2010-03.csv;