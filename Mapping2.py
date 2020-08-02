import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import WordPunctTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords 
import spacy
from nltk.stem import PorterStemmer
from spacy.lang.en.stop_words import STOP_WORDS
from nltk.stem import LancasterStemmer
import csv
import os
from fuzzywuzzy import process
from fuzzywuzzy import fuzz
import numpy as np

#MUST DO THIS IN CMD
#python -m spacy download en_core_web_md

#INPUTS
#INPUT_FILE = "New-Admit-Reject-Data.csv"  
#target_column = 'University Applied'  #column to map
#KEYWORD_FILE = 'University Keyword Mapping.xlsx'

#OUTPUT_FILE = 'Admit-Reject-Data-with-Univ-ID.csv'

nlp = spacy.load('en_core_web_md')
porter = PorterStemmer()
stop_words = set(stopwords.words('english'))

#common_words = ['school','univers','Of','Of','of','colleg','the','institut']
common_words = ['or']
    
def remove_duplicates(x):
  return list(dict.fromkeys(x))

def get_unique_names(df,target_column):

    columns_name = list(df.columns)
    
    if target_column not in columns_name:
      print("Target Column not in INPUT FILE")
      
    df = df[[target_column]]
    df.drop_duplicates(subset = target_column, inplace = True)
    print(df.describe())
    return df
  
def map_univ(INPUT_FILE,target_column,KEYWORD_FILE,OUTPUT_FILE):

  get_file_type = OUTPUT_FILE.split(".")
  if get_file_type[1] != "csv":
    print("OUTPUT File type not supported. Only .csv")
    return
        
  keyword_file_exists = os.path.isfile(KEYWORD_FILE)
  if not keyword_file_exists:
    print("KEYWORD File doesn't exists")
    return

  input_file_exists = os.path.isfile(INPUT_FILE)
  if not input_file_exists:
    print("INPUT File doesn't exists")
    return


  #Build keywords for univ. names
  file = pd.read_excel(KEYWORD_FILE,headers = ['University Name','Campus','_id','Country','Campus Edit'])
  file.fillna('')

  headers_list = list(file.columns)
  
  univ_keywords_df = pd.DataFrame(columns = headers_list)
  country_dict = {}
  univ_id_dict = {}
  
  file = file.replace(np.nan, '', regex=True)
  for index,row in file.iterrows():
    univ_name = str(row['University Name'])
    campus=""

    campus = str(row['Campus'])    
      
    country_dict.update({row['Country'] : 0})
    
    univ_id_dict.update ({  univ_name + ',' + campus : row["_id"]})

    univ_keywords_df = univ_keywords_df.append({'University Name': univ_name , 'Campus': campus , '_id' : row["_id"], 'Country' : row['Country'],
                                       'Campus Edit' : row['Campus Edit']},ignore_index=True)

  
  #univ_keywords_df.to_excel("Univ Keyword Mapping.xlsx",engine="xlsxwriter")
  country_univ={}
  for key,val in country_dict.items():
    country_univ.update({key:[]})
  for index , row in univ_keywords_df.iterrows():
    for key,val in country_univ.items():
      if key==row['Country']:
        country_univ[key].append( str(str(row['University Name']) + ',' + str(row['Campus'])))
    

  get_file_type = INPUT_FILE.split(".")
  input_dataframe = pd.DataFrame()

  if get_file_type[1]=="csv":
    input_dataframe = pd.read_csv(INPUT_FILE,engine='python')
  elif get_file_type[1]=="xlsx":
    input_dataframe = pd.read_excel(INPUT_FILE)
  else:
    print("File type not supported")
    

  def get_key(val):
      for key, value in country_univ.items(): 
           if val in value: 
               return key
      return 0
              
  all_univ_names=[]
  for index,row in univ_keywords_df.iterrows():   
    all_univ_names.append(str(row['University Name']) + ',' + str(row['Campus']))

  file_exists = os.path.isfile(OUTPUT_FILE)

  output_headers = []
  for header in input_dataframe.columns:
    output_headers.append(header)

  output_headers.append ('Mapped Univ Name')
  output_headers.append ('Campus')
  output_headers.append ('Score')
  output_headers.append ('Univ ID')
  output_headers.append ('Country')
  
  unique_input_df = get_unique_names(input_dataframe,target_column)
  unique_input_df = unique_input_df.replace(np.nan, '', regex=True)
  print(unique_input_df)
  
  dict_mapping = {}
  for index , row in unique_input_df.iterrows():
    try:
      highest1 = process.extractOne(row[target_column],all_univ_names)
      #highest2 = process.extractOne(row[target_column],all_univ_names,scorer=fuzz.ratio)
      #highest3 = process.extractOne(row[target_column],all_univ_names,scorer = fuzz.token_sort_ratio)
      #highest4 = process.extractOne(row[target_column],all_univ_names,scorer = fuzz.partial_ratio)
      #highest5 = process.extractOne(row[target_column],all_univ_names,scorer=fuzz.token_set_ratio)
      
      if int(highest1[1])>=90:
        mapped_name = [highest1[0].split(',')[0], highest1[0].split(',')[1] , highest1[1] , univ_id_dict[highest1[0]], get_key(highest1[0])]
        print(row[target_column],mapped_name)
        dict_mapping.update({row[target_column] : mapped_name })
      #else:
       # pass
        '''
        if int(highest2[1])>=87 and highest4[1]>80:
          mapped_name = [highest2[0].split(',')[0], highest2[0].split(',')[1] , highest2[1] , univ_id_dict[highest2[0]], get_key(highest2[0])]
          print(row[target_column],mapped_name)
          dict_mapping.update({row[target_column] : mapped_name })
        else:
          avg = (highest5[1]+highest4[1])/2
          if avg>=90.5:
            mapped_name = [highest5[0].split(',')[0], highest5[0].split(',')[1] , highest5[1] , univ_id_dict[highest5[0]], get_key(highest5[0])]
            print(row[target_column],mapped_name)
            dict_mapping.update({row[target_column] : mapped_name })
        '''
                
        
    except Exception as e:
      print(e)

 
  def getList(dict_mapping):
    return list(dict_mapping.keys())
  
  all_mapped_spec = getList(dict_mapping)

  df = pd.DataFrame.from_dict(dict_mapping,orient='index',columns=['Mapped University','Campus', 'Score', 'Univ ID' ,'Country'])
  df.to_csv("Check_Mapped_Universities.csv")
  
  with open(OUTPUT_FILE,'a',newline="") as file:
    csvwriter = csv.writer(file)
    if not file_exists:
      csvwriter.writerow(output_headers)
    
  all_mapped_univ = getList(dict_mapping)
  
  for index , row in input_dataframe.iterrows():
    with open(OUTPUT_FILE,'a',newline="") as file:
      csvwriter = csv.writer(file)
      if row[target_column] not in all_mapped_univ:
        try:
          input_file_row=row.values.tolist()
          input_file_row.append('')
          input_file_row.append('')
          input_file_row.append('')
          input_file_row.append('')
          input_file_row.append('')
          csvwriter.writerow(input_file_row)
          print(input_file_row)
        except:
          pass
      else:
        try:
          input_file_row=row.values.tolist()
          for values in dict_mapping[row[target_column]]:
            input_file_row.append(values)
          csvwriter.writerow(input_file_row)
        except:
          pass
        
 
                  
    
       
    
                
                     
        
    
        
        
   
 
     

