####################################
###### FORMULAIRE PEDAGOGIQUE ######
####################################

===================================================================================================
VERSIONS
===================================================================================================

Python version : 3.7 ou 3.8
Python library :
flask 1.1.2
plotly. 3.0.0
pandas 1.0.4
mysql.connector 2.2.9

===================================================================================================
ARBORESCENCE
===================================================================================================

Fichiers :
app.py
db.py
templates/
    formation_date.html
    formulaire_pedag.html
    nom_formation.html
    tableau.html
static/
    logo.cefim.png
    
===================================================================================================
INSTALLATION
===================================================================================================

Pour l'installation de l'application sur le serveur,
Il faut tout d'abord installer Python, les versions 3.7 et 3.8 ont été testées et elles sont compatibles.
L'installation des library notifiées plus haut est nécessaire, excecutez le fichier requirements.txt.
Utilisez pip install requirements.txt
Installez ensuite app.py puis db.py et enfin templates/formulaire_pedag.html à l'endroit désiré.
Importez le dump SQL dans une base de données MySQL nommé 'evalutation'.
Connectez votre base de données en modifiant db.py.
Placez vous dans le dossier ou vous avez installé app.py et lancez le script à l'aide de la commande "python app.py"
Rendez vous sur l'adresse http://localhost:5000/ par défaut.

