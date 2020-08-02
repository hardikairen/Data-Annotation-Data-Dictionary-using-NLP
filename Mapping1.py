import pandas as pd
import nltk
from nltk.tokenize import word_tokenize
from nltk.tokenize import WordPunctTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords 
import spacy
from nltk.stem.snowball import SnowballStemmer
from spacy.lang.en.stop_words import STOP_WORDS 
import csv
import os
from fuzzywuzzy import process
from fuzzywuzzy import fuzz

#MUST DO THIS IN CMD
#python -m spacy download en_core_web_md

#INPUTS
#INPUT_FILE = "SKILLS REPORT.xlsx" #must have column named "Skill Set"
#KEYWORD_FILE = 'Course Keyword Mapping.xlsx'
#threshold = 1  #How many maximum specialisations to map for a particular skill (based on score of keywords)
#OUTPUT_FILE = 'SKILLS REPORT with Specialisation Mapped.xlsx'

nlp = spacy.load('en_core_web_md')
porter = SnowballStemmer("english")
stop_words = set(stopwords.words('english'))

def remove_duplicates(x):
  return list(dict.fromkeys(x))

def get_keywords(mystring):
  
  mystring = word_tokenize(mystring.lower())
  key_list=[]
  for word in mystring:
    if word not in stop_words:
      if str(word).strip() not in [',','','nan','and','&',"'",':',';','(',')','/']:
        key_list.append(str(word).strip())
        
  return key_list

def get_unique_names(df,target_column):

    columns_name = list(df.columns)
    
    if target_column not in columns_name:
      print("Target Column not in INPUT FILE")
      
    df = df[[target_column]]
    df.drop_duplicates(subset = target_column, inplace = True)
    print(df.describe())
    return df
  
def map_specialisation(INPUT_FILE , KEYWORD_FILE , target_column , threshold , OUTPUT_FILE):

  
  get_file_type = OUTPUT_FILE.split(".")
  if get_file_type[1] != "csv":
      print("OUTPUT File type not supported. Only .csv")
        
  keyword_file_exists = os.path.isfile(KEYWORD_FILE)
  if not keyword_file_exists:
    print("File doesn't exists")

  input_file_exists = os.path.isfile(INPUT_FILE)
  if not input_file_exists:
    print("File doesn't exists")

  
  file = pd.read_excel(KEYWORD_FILE,headers = ['area','specialisation','keywords1','keywords2','keywords3'])
  file.fillna(' ')
                   
  mapping_df = pd.DataFrame(columns=['AOS','Specialisation','Spec. Keywords','Keywords1','Keywords2','Keywords3'])
  aos_dict= {}

  for index , row in file.iterrows():
      keyword_list1= str(row[2]).split(',')  #keywords with score 200
      keyword_list2 = str(row[3]).split(',') #keywords with score 150
      keyword_list3 = str(row[4]).split(',') #keywords with score 100
      keyword_list1 =  list(filter(None, keyword_list1))
      keyword_list2 =  list(filter(None, keyword_list2)) 
      keyword_list3 =  list(filter(None, keyword_list3)) 

      #get all aos in a dictionary
      aos_dict.update({row[0] : 0})

      all_keywords = []
      all_keywords.append(keyword_list1)
      all_keywords.append(keyword_list2)
      all_keywords.append(keyword_list3)

      #all_keywords = remove_duplicates(all_keywords)
      keywords_list=[]
      unique_keywords = []
      for each_list in all_keywords:
        key_list=[]
        for i in each_list:
          i = i.lower()
          j = word_tokenize(i)
          for token in j:
            if token not in stop_words:
              if str(token).strip() not in [',','','nan','and','&',"'",':',';','(',')','/']:
                #key_word = porter.stem(token)
                if token not in unique_keywords:
                  key_list.append(str(token))
                  unique_keywords.append(token)
                    
        key_list = remove_duplicates(key_list)
        keywords_list.append(key_list)

      #get keywords of specialisation  name
      #spec_words = get_keywords(str(row[1]))
      #spec_words = remove_duplicates(spec_words)

      spec_keywords = get_keywords (str(row[1]).lower())
      spec_keywords = remove_duplicates(spec_keywords)
      mapping_df = mapping_df.append({'AOS': row[0].strip() , 'Specialisation': row[1].strip(),'Spec. Keywords': spec_keywords , 'Keywords1' : keywords_list[0], 'Keywords2' : keywords_list[1],
                                      'Keywords3' : keywords_list[2]},ignore_index=True)


  #map aos with specialisation
  aos_spec={}
  for key,val in aos_dict.items():
    aos_spec.update({key:[]})
  for index , row in mapping_df.iterrows():
    for key,val in aos_spec.items():
      if key==row[0]:
        aos_spec[key].append(row[1])
    
   
  mapping_df.to_excel('Course Keyword Mapping using NLP.xlsx',engine='xlsxwriter')

  
    
  get_file_type = INPUT_FILE.split(".")
  input_dataframe = pd.DataFrame()
  
  if get_file_type[1]=="csv":
    input_dataframe = pd.read_csv(INPUT_FILE,engine='python')
  elif get_file_type[1]=="xlsx":
    input_dataframe = pd.read_excel(INPUT_FILE)
  else:
    print("File type not supported.Only .xlsx or .csv")

  spec_mapped_data=[]
  headers_list = []
   
  def get_key(val,dictionary):
    for key, value in dictionary.items():
      if val in value:
        return key
      
  output_headers = []
  for header in input_dataframe.columns:
    output_headers.append(header)

  output_headers.append ('Mapped AOS')
  output_headers.append ('Mapped Specialisation')
  output_headers.append ('Score')

  
  unique_input_df = get_unique_names(input_dataframe,target_column)
  print(unique_input_df)
         
  count=1
  file_exists = os.path.isfile(OUTPUT_FILE)
  
  dict_mapping = {}
  spec_string_dict={}
    
  for index , row in unique_input_df.iterrows():
    mapped_skill= {}
    sort_mapped_skill= []  #specialisation mapped with score dictionary
    sort_aos_dict= []   #aos with keyword score dictionary
    temp_aos_dict = dict(aos_dict)
    skill_words = get_keywords (str(row[target_column].strip().lower()))
    skill_words = remove_duplicates(skill_words)
    try:
      if row[target_column].strip().lower() in list(mapping_df['Specialisation'].str.lower()):
        print(row[target_column].lower())
        mapped_skill.update({row[target_column] : 5000 })

      else:
        highest1 = process.extractOne(row[target_column] ,list(mapping_df['Specialisation']))
        if highest1[1]>=90:
          mapped_skill.update({highest1[0] : 2000})
          
                                   
        max_found=0
        for index,rows in mapping_df.iterrows():
          found=0
          for words in skill_words:
            if words in rows[2]:
              found=found+1

          if found==len(rows[2]) and found>max_found:
            max_found = found
            mapped_skill.update({rows[1] : 1000 })
        
      x=0
      for index,map_row in mapping_df.iterrows():
        x=0
        for word in skill_words:       #check for words in a dictionary and assign scores
          if word in map_row[3]:
            x+=200
            if word not in ['engineering']:
              temp_aos_dict[map_row[0]]+= map_row[2].count(word)    
          if word in map_row[4]:
            x+=150
            if word not in ['engineering']:
              temp_aos_dict[map_row[0]]+= map_row[3].count(word)
          if word in map_row[5]:
            x+=100
            if word not in ['engineering']:
              temp_aos_dict[map_row[0]]+= map_row[4].count(word)
        if x>=200:   
          mapped_skill.update({map_row[1] : x })

      sort_aos_dict = sorted(temp_aos_dict.items(), key=lambda x: x[1], reverse = True) 
      sort_mapped_skill = sorted(mapped_skill.items(), key=lambda x: x[1], reverse=True)
      val=1
      #sort the dictionary on the basis of keyword score
      for i in sort_mapped_skill:
        if val<= threshold:
          try:
            print(row[target_column] , get_key(i[0],aos_spec) ,i[0], i[1],skill_words)
            mapped_name = [get_key(i[0],aos_spec) , i[0],i[1],skill_words ]
            dict_mapping.update({row[target_column] : mapped_name })
          except Exception as er:
            print(er)
          
        val+=1
    except Exception as error:
      print(error)
  
  
  def getList(dict_mapping):
    return list(dict_mapping.keys())
  
  all_mapped_spec = getList(dict_mapping)

  df = pd.DataFrame.from_dict(dict_mapping,orient='index',columns=['Mapped AOS', 'Mapped Spec' ,'Score','Keywords'])
  df.to_csv("Check_Specialisation_Mapping.csv")

  return 0

  with open(OUTPUT_FILE,'a',newline="") as file:
    csvwriter = csv.writer(file)
    if not file_exists:
      csvwriter.writerow(output_headers)
    
  for index , row in input_dataframe.iterrows():
    with open(OUTPUT_FILE,'a',newline="") as file:
      csvwriter = csv.writer(file)
      if row[target_column] not in all_mapped_spec:
        try:
          input_file_row=row.values.tolist()
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
               



                
   



    
    
    
       
    
                
                     
        
    
        
        
   
 
     

