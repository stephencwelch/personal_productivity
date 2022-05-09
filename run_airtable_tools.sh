#!/bin/sh  
while true  
do  
  echo "RUNNING..."
  jupyter nbconvert --ExecutePreprocessor.timeout=600 --to pdf --execute airtable_utilites_v1.ipynb  
  sleep 600 
done
