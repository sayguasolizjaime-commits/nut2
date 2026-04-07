import os
import pandas as pd

archivo = "base.xlsx - base.csv"
if os.path.exists(archivo):
    df_base = pd.read_csv(archivo)
else:
    st.error(f"El archivo {archivo} no se encuentra en la ruta actual: {os.getcwd()}")