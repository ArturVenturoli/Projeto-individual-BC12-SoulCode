# -*- coding: utf-8 -*-
"""Projeto_Artur_Venturoli_BC12_ENG_DE_DADOS.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/10MBvg14zX7dBvw_cBxv1C3gDrmx2oIJU

#**01.Instalações e importações**

Install PySpark
"""

!pip install pyspark

"""Install GCP"""

!pip install gcsfs

"""Install Mongo"""

pip install pymongo[srv]

"""install MySQL"""

!pip install mysql-connector-python

"""Import PySpark SQL / Pandas / GCP"""

from pyspark.sql import SparkSession
from pyspark import SparkConf
import pyspark.sql.functions as F
from pyspark.sql.types import *
from pyspark.sql.window import Window

import pandas as pd

from google.cloud import storage
import os

"""Import Mogo"""

import pymongo
from pymongo import MongoClient

"""Import MySQL"""

import mysql.connector
from mysql.connector import Error

"""#**02.Autenticação de segurança e Conexões**

---
a ou b

**a. Autenticação de úsuario - GCP**

---
https://colab.research.google.com/notebooks/io.ipynb#scrollTo=eikfzi8ZT_rW
"""

# Não executei para não solicitar autenticação.
from google.colab import auth
auth.authenticate_user('p_12_av_k')

"""Keys - GCP"""

# Editei o acesso da chave para público
serviceAccount = "gs://p_12_av_k/uplifted-stream-339219-41de153edd08.json"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = serviceAccount

"""**b. Autenticação de usuário Local**"""

from google.colab import drive
drive.mount('/content/drive/')

"""Key"""

serviceAccount = "/content/drive/MyDrive/keys_bc12/uplifted-stream-339219-41de153edd08.json"

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = serviceAccount

"""**2.1. Conectar Atlas MongoDb**"""

client = pymongo.MongoClient("path")

db = client['aulamongo']
colecao_av_bruto = db.bc12_av_bruto

db = client['aulamongo']
colecao_av_tratado = db.bc12_av_tratado

"""**2.2. Conectar GCP**"""

client = storage.Client()

bucket = client.get_bucket('projeto_bc12_av') # Nome da bucket
bucket.blob('marketing_campaign.csv') #Nome do arquivo na bucket
path = 'gs://projeto_bc12_av/bruto/marketing_campaign.csv' # Endereço Gsutil do arquivo na bucket

"""**2.3. Conectar MySQL**"""

conexao = mysql.connector.connect("host, user, password, db")

def conexao_db(host, user, password, db):
  conexao = None
  try:
    conexao = mysql.connector.connect(
        host = host,
        user = user,
        passwd = password,
        database =  db
    )
    print(f"Conexão com o banco {db} realizada com sucesso!")
  except:
    print(f"Erro ao conectar ao banco {db}! '{Error}'")

  return conexao

conexao = conexao_db("host, user, password, db")

"""#**3. Exibir todas as colunas sem '...'**"""

pd.set_option('max_columns', None)

"""#**4. SparkSession**"""

spark = (SparkSession.builder
        .master("local")
        .appName("projeto_bc12_artur_venturoli")
        .config('spark.ui.port', '4050')
        .config("spark.jars", 'https://storage.googleapis.com/hadoop-lib/gcs/gcs-connector-hadoop2-latest.jar')
        .getOrCreate())

spark

"""#**5. Dataset e Backup**

Optei por renomear o arquivo afim de evitar imcompatibilidade em sua execução. Remoção de pontos no nome do arquivo.
- De: 
'marketing_campaign.csv - marketing_campaign.csv.csv'
- Para: 'marketing_campaign.csv'

**5.1. Dataset Pandas**
"""

df_origem = pd.read_csv("gs://projeto_bc12_av/bruto/marketing_campaign.csv",sep=",")

"""**5.2. Backup Dataset**

---
Criando uma cópia para trabalhar, mantendo assim o arquivo original integro.

"""

df = df_origem.copy()

"""**5.3. Backup Dataset bruto para Mongo**"""

# Converte DataFrame em dicionário
df_to_mongo_origem = df_origem.to_dict('records')
# Insere no DB
colecao_av_bruto.insert_many(df_to_mongo_origem)

"""#**6. Tratamento**

##**6.1. Tradução**

---
Primeiramente, busquei compreender o significado de cada atributo/coluna para tomada de decisões Ao pesquisar o termo "AcceptedCmp3" cheguei ao link que continha informações sobre o significado da maioria deles. Link: https://www.kaggle.com/rodsaldanha/targeted-marketing-campaign/data

---
- **Atributos/Colunas**
- **Valores dos Atributos/Colunas:** 'Education':'formac_academica', 'Marital_Status':'estado_civil'
"""

df.head(5)

df.info()

#Auxilio para analise: Trás todos os valores sem repeti-los
sorted(pd.unique(df['formac_academica']))

sorted(pd.unique(df['estado_civil']))

#Auxilio para analise: se há valores nulos na coluna
df.isna().sum()

"""##**6.2. Apagando atributos/colunas:** 

---
Com a falta de significado na tradução, analisei a relevancia dos valores contidos em alguns atributos, optando por apagar alguns. **No caso do atributo 'Response'** com base em seu significado: 'se o cliente aceitou a oferta na última campanha', por não ficar claro qual a campanha que se trata, podendo ser entre a primeira e a quinta, exclui-o.

---
Atributos excluidos:
- 'Z_CostContact'
- 'Z_Revenue'
- 'Response'

###*6.2.1. Analizando...*
"""

#Auxilio para analise
df.head(2)

#Auxilio para analise: se há valores únicos na coluna
df.Response.is_unique

#Auxilio para analise: se há valores nulos na coluna
df.isna().sum()

#Auxilio para analise: Trás todos os valores sem repetilos
sorted(pd.unique(df['Response']))

"""###*6.2.3. Apagando atributos/colunas*"""

df.drop(['Z_CostContact','Z_Revenue','Response'],axis=1, inplace=True)

# Verificarndo o resultado
df.head(2)

"""##**6.3. Renomeando os atributos/colunas e valores**

###*6.3.1. Renomeando os atributos/colunas*

---
Os nomes para os atributos foram beseados pelos siginificados da tradução.
"""

(df.rename(columns={'ID':'id_cliente',
                    'Year_Birth':'ano_nasc_cliente',
                    'Education':'formac_academica',
                    'Marital_Status':'estado_civil',
                    'Income':'renda_anual',
                    'Kidhome':'num_crianca_em_casa',
                    'Teenhome':'num_adolecente_em_casa',
                    'Dt_Customer':'data_cadastro_cliente',
                    'Recency':'ultm_comp_a_x_dia',
                    'MntWines':'v_gasto_produt_base_uva',
                    'MntFruits':'v_gasto_produt_fruta',
                    'MntMeatProducts':'v_gasto_produt_carne',
                    'MntFishProducts':'v_gasto_produt_pescado',
                    'MntSweetProducts':'v_gasto_produt_doce',
                    'MntGoldProds':'v_gasto_produt_ouro',
                    'NumDealsPurchases':'num_comp_com_desc',
                    'NumWebPurchases':'num_comp_site_empr',
                    'NumCatalogPurchases':'num_comp_por_catalogo',
                    'NumStorePurchases':'num_comp_na_loja',
                    'NumWebVisitsMonth':'visita_site_empr_ultm_mes',
                    'AcceptedCmp3':'comp_3_oferta',
                    'AcceptedCmp4':'comp_4_oferta',
                    'AcceptedCmp5':'comp_5_oferta',
                    'AcceptedCmp1':'comp_1_oferta',
                    'AcceptedCmp2':'comp_2_oferta',
                    'Complain':'reclamacao_cliente'
},inplace=True)
)

df.ID.is_unique

df.head(2)

"""###*6.3.2. Renomeando valores*"""

#Backup da coluna
df['bkp_formac_academica'] = df.formac_academica

#Backup da coluna
df['bkp_estado_civil'] = df.estado_civil

df.head(2)

# Renomear valores da coluna 'formac_academica'
df.formac_academica.replace(to_replace=['2n Cycle', 'Basic', 'Graduation', 'Master', 'PhD'],value=['colegial','basico','graduacao','mestre','doutorado'],inplace=True)

# Renomear valores da coluna 'estado_civil'
(df.estado_civil.replace(
    to_replace=['Absurd','Alone','Divorced','Married','Single','Together','Widow','YOLO'],
    value=['desconectada_o','sozinha_o','divorciada_o','casada_o','solteira_o','junto','viuva_o','irrefletida_o'],
    inplace=True)
)

#Auxilio para analise: Trás todos os valores sem repetilos
sorted(pd.unique(df['formac_academica']))

#Excluindo as colunas de Bacukp
df.drop(columns='bkp_formac_academica',inplace=True)

#Excluindo as colunas de Bacukp
df.drop(columns='bkp_estado_civil',inplace=True)

df.head(2)

"""##**6.4. Analisando outros dados**

###6.4.1. Dados inconcistentes NaN ou NA

---
A única coluna com com valore nulos é a 'renda_anual'. Isso demonstra que alguns clientes possivelmente não tem renda ou simplesmente optaram por não declarar. Sendo assim atrinui o valor '0'.
"""

#Backup da coluna antes de alterar valores
df['bkp_renda_anual'] = df.renda_anual

# Alterar valor nulo para 0 'formac_academica'
df.renda_anual.fillna(0,inplace=True)

#Excluindo as colunas de Bacukp
df.drop(columns='bkp_renda_anual',inplace=True)

df.head(2)

df.renda_anual.isna().sum()

df.isna().sum()

df.count()

#Auxilio para analise: Trás todos os valores sem repetilos
sorted(pd.unique(df['reclamacao_cliente']))

"""###6.4.2. Colunas: comp_1_oferta / comp_2_oferta / comp_3_oferta / comp_4_oferta / comp_5_oferta

---
Enquanto realizava a tradução identifiquei que os valores das colunas acima corresponde a: ‘1 = Sim’ e ‘2 = Não’

---
Link: https://www.kaggle.com/code/rodsaldanha/targeted-marketing-campaign/data

####6.4.2.1. Backup das colunas antes de anterar valores • PLAY •
"""

df['bkp_comp_1_oferta'] = df.comp_1_oferta

df['bkp_comp_2_oferta'] = df.comp_2_oferta

df['bkp_comp_3_oferta'] = df.comp_3_oferta

df['bkp_comp_4_oferta'] = df.comp_4_oferta

df['bkp_comp_5_oferta'] = df.comp_5_oferta

"""####6.4.2.2. Renomear valores das colunas •PLAY•"""

# Renomear valores da coluna
df.comp_1_oferta.replace(to_replace=[0,1],value=['nao','sim'],inplace=True)

df.comp_2_oferta.replace(to_replace=[0,1],value=['nao','sim'],inplace=True)

df.comp_3_oferta.replace(to_replace=[0,1],value=['nao','sim'],inplace=True)

df.comp_4_oferta.replace(to_replace=[0,1],value=['nao','sim'],inplace=True)

df.comp_5_oferta.replace(to_replace=[0,1],value=['nao','sim'],inplace=True)

"""####6.4.2.3. Excluindo as colunas de Bacukp •PLAY•"""

df.drop(columns='bkp_comp_1_oferta',inplace=True)

df.drop(columns='bkp_comp_2_oferta',inplace=True)

df.drop(columns='bkp_comp_3_oferta',inplace=True)

df.drop(columns='bkp_comp_4_oferta',inplace=True)

df.drop(columns='bkp_comp_5_oferta',inplace=True)

"""#**7. Exportando Dataframe Pandas** 

---
Após comcluir algumas etapas com pandas, realizei a exportação em buma bucket específica, possibilitando a importação na sequência para continuar outros tratamentos em com pyspark.

"""

df.to_csv('gs://projeto_bc12_av/tratamento/analise_campanhas_de_marketing_pandas.csv', index=False)

"""#**8. StructType / Importando DataFrame para PySpark**

##**8.1. StructType** >>NÂO FUNCIONA<<
"""

esquema = (
    StructType([
                StructField('apagar',IntegerType(), True),
                StructField('id_cliente',IntegerType(), True),
                StructField('ano_nasc_cliente',IntegerType(), True),
                StructField('formac_academica',StringType(), True),
                StructField('estado_civil',StringType(), True),
                StructField('renda_anual',FloatType(), True),
                StructField('num_crianca_em_casa',IntegerType(), True),
                StructField('num_adolecente_em_casa',IntegerType(), True),
                StructField('data_cadastro_cliente',StringType(), True),
                StructField('ultm_comp_a_x_dia',IntegerType(), True),
                StructField('v_gasto_produt_base_uva',IntegerType(), True),
                StructField('v_gasto_produt_carne',IntegerType(), True),
                StructField('v_gasto_produt_pescado',IntegerType(), True),
                StructField('v_gasto_produt_doce',IntegerType(), True),
                StructField('v_gasto_produt_ouro',IntegerType(), True),
                StructField('num_comp_com_desc',IntegerType(), True),
                StructField('num_comp_site_empr',IntegerType(), True),
                StructField('num_comp_por_catalogo',IntegerType(), True),
                StructField('num_comp_na_loja',IntegerType(), True),
                StructField('visita_site_empr_ultm_mes',IntegerType(), True),
                StructField('comp_1_oferta',StringType(), True),
                StructField('comp_2_oferta',StringType(), True),
                StructField('comp_3_oferta',StringType(), True),
                StructField('comp_4_oferta',StringType(), True),
                StructField('comp_5_oferta',StringType(), True),
                StructField('reclamacao_cliente',IntegerType(), True)
    ])
)

"""##**8.2. Importando DataFrame para PySpark**"""

dfs = ( spark.read
            .format('csv')
            .option('header', 'true')
            .option('delimiter', ',')
            .option('inferschema', 'true')
            .load('gs://projeto_bc12_av/tratamento/analise_campanhas_de_marketing_pandas.csv')
)

dfs.printSchema()

dfs.toPandas()

"""#**9. Valores nulos e outras inconsistências**

##**9.1. Verificação de valores nulos**

---
Não foram encontrados valores nulos. Esse tratamento foi realizado em pandas.
"""

dfs.toPandas().isna().sum()

"""##**9.2 Inconcistências**

---
- Ordenar ordem de algumas colunas

"""

dfs.toPandas().head(2)

"""###9.2.1. Ordernar colunas

---
Algumas colunas não estavam adequadas em sua ordem
"""

dfs2 = (dfs.select([
             F.col('id_cliente'),F.col('ano_nasc_cliente'),F.col('formac_academica'),F.col('estado_civil'),F.col('renda_anual'),
             F.col('num_crianca_em_casa'),F.col('num_adolecente_em_casa'),F.col('data_cadastro_cliente'),F.col('ultm_comp_a_x_dia'),
             F.col('v_gasto_produt_base_uva'),F.col('v_gasto_produt_fruta'),F.col('v_gasto_produt_carne'),F.col('v_gasto_produt_pescado'),
             F.col('v_gasto_produt_doce'),F.col('v_gasto_produt_ouro'),F.col('num_comp_com_desc'),F.col('num_comp_site_empr'),
             F.col('num_comp_por_catalogo'),F.col('num_comp_na_loja'),F.col('visita_site_empr_ultm_mes'),F.col('comp_1_oferta'),
             F.col('comp_2_oferta'),F.col('comp_3_oferta'),F.col('comp_4_oferta'),F.col('comp_5_oferta'),F.col('reclamacao_cliente')])
)
dfs2.show()

dfs2.toPandas().head(2)

"""#10. Drop

---
Não identifiquei a necessidade de realizar o Drop em linhas. Quanto as colunas, realizei em Pandas (item 6.2.3.).

#11. Renomear colunas
"""

dfs2.toPandas().head(2)

"""##**Colunas renomeadas 01**"""

dfs3 = (dfs2.withColumnRenamed("comp_1_oferta","comp_feita_camp1")
 .withColumnRenamed("comp_2_oferta","comp_feita_camp2")
 .withColumnRenamed("comp_3_oferta","comp_feita_camp3")
 .withColumnRenamed("comp_4_oferta","comp_feita_camp4")
 .withColumnRenamed("comp_5_oferta","comp_feita_camp5")
 )
dfs3.show()

dfs3.toPandas().head(2)

"""##**Colunas renomeadas 02**"""

dfs4 = (dfs3.withColumnRenamed("num_comp_com_desc","comp_com_desc")
 .withColumnRenamed("num_comp_site_empr","comp_site_empr")
 .withColumnRenamed("num_comp_por_catalogo","comp_por_catalogo")
 .withColumnRenamed("num_comp_na_loja","comp_na_loja")
 .withColumnRenamed("num_crianca_em_casa","crianca_em_casa")
 .withColumnRenamed("num_adolecente_em_casa","adolecente_em_casa")
 )
dfs4.show()

dfs4.toPandas().head(2)

"""#**12. Agrupamento / Agregação / Join**

##**12.1. Criando uma nova coluna com base em mais de duas condições**

---
A nova coluna identifica a geração de cada cliente com base em seu ano de nascimento (coluna: ‘ano_nasc_cliente’).
"""

dfs5 = (dfs4.withColumn("geracao", F.when((F.col('ano_nasc_cliente') >= 1945) & (F.col('ano_nasc_cliente') <= 1963), F.lit('Baby_Boomers'))
                                .when((F.col('ano_nasc_cliente') >= 1964 ) & (F.col('ano_nasc_cliente') <= 1980), F.lit('Geracao_X'))
                                .when((F.col('ano_nasc_cliente') >= 1981 ) & (F.col('ano_nasc_cliente') <= 1997), F.lit('Geracao_Y'))
                                .when((F.col('ano_nasc_cliente') >= 1998 ) & (F.col('ano_nasc_cliente') <= 2009), F.lit('Geracao_Z'))
                                .otherwise(F.lit('Geracao_Z'))))
dfs5.show()

dfs5.toPandas()

"""##**12.2. Agregação** (Há um df unico aqui)

---
Aqui é gerada informações referentes a soma da renda anual da agregação de cada geração, além da renda anual máxima, mínima e média.

"""

dfs6 = (dfs5.groupBy(F.col("geracao"))
          .agg(F.sum(("renda_anual")),
          F.max(("renda_anual")),
          F.min(("renda_anual")),
          F.avg("renda_anual"))
)
dfs6.show()

dfs6.toPandas()

"""#**13. Filtros**

##**13.1. Exibir a geração e formação academica das pessoas casadas**
"""

dfs5.select(F.col('estado_civil'), F.col('geracao'), F.col('formac_academica')).filter(F.col('estado_civil') == "casada_o").show(20)

"""##**13.2. Clientes que compraram produtos a base de uva na primeira campanha no valor superior a 100.**"""

dfs5.filter((F.col("comp_feita_camp1") == "sim") & (F.col("v_gasto_produt_base_uva") >= 100)).show()

dfs5.toPandas()

"""#**14. Window Functions**

##**14.1. rank**
"""

wc = Window.partitionBy(F.col('estado_civil')).orderBy('crianca_em_casa')

dfs5.withColumn('rank', F.rank().over(wc)).show()

"""##**14.2. dense_rank**"""

wgra = Window.partitionBy(F.col('geracao')).orderBy('renda_anual')

dfs5.withColumn('dense_rank', F.dense_rank().over(wgra)).show()

"""#**15. SparkSQL**"""

def executar_query(conexao, sql): # conexao é a variavel global - sql é o comando que queremos
  cursor = conexao.cursor()
  try:
    cursor.execute(sql) # Executa / cursor (objeto do sql) === herança
    conexao.commit() # confirma execução no banco de dados
    print("Query executada com Sucesso!")
  except Error as err: # Mensagem de erro de execução
    print(f"Erro ao executar a query! {err}")

def ler_query(conexao, sql):
  cursor = conexao.cursor() # objeto do MySQL
  resultado = None
  try:
    cursor.execute(sql)
    resultado = cursor.fetchall() # o metodo fetchall retorna todas as consultas ao banco
    return resultado
  except Error as err:
    print(f"Erro ao listar do banco de dados - '{err}'")

"""##**15.1. Consulta 1**"""

select = 'SELECT * FROM dfs5 ORDER BY renda_anual DESC'
ler = ler_query(conexao,select)

print(select)

"""##**15.1. Consulta 2**

##**15.1. Consulta 3**

##**15.1. Consulta 4**

##**15.1. Consulta 5**

#**16. Salvando Dataframe Tratado no CloudStorage e MongoDB**

##**16.1. Dataframe Tratado CloudStorage**
"""

dfs5.write.csv('gs://projeto_bc12_av/final/analise_campanhas_de_marketing_final.csv')

"""##**16.2. Dataframe Tratado no MongoDb**"""

dfs5.toPandas().head(2)

# Converte DataFrame em dicionário
df_to_mongo = dfs5.to_dict('records')
# Insere no DB
colecao_av_tratado.insert_many(df_to_mongo)

dfs5.bc12_av_tratado.format("mongo").mode("append").save()