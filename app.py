from flask import Flask, render_template, request, jsonify
import plotly.express as px
from plotly.io import to_json
import pandas as pd
from db import init_app, get_db

app = Flask(__name__)
init_app(app)


@app.route('/', methods=['GET', 'POST'])
def route_principale():
    """
    Name: route_principale
    Objet: Affiche la page principale avec les filtres sur la date, la formation et les étudiants
    :return: Renvoi vers 'formulaire_pedag' pour traitement des selects
    """
    conn = get_db()
    cur = conn.cursor()
    # Requête SQL pour récupérer le nom, prenom, la formation et son ID, et l'année de la promotion.
    cur.execute("""
                SELECT session.id,
                reponse_nom.texte AS Nom,
                reponse_prenom.texte AS Prénom,
                choix_formation.choix_id AS Formation,
                choix.libelle as libelle_formation,
                YEAR(session.date) AS Promotion
                FROM session
                INNER JOIN reponse AS reponse_nom
                    ON reponse_nom.session_id = session.id
                    AND reponse_nom.question_id = 2
                 INNER JOIN reponse AS reponse_prenom
                    ON reponse_prenom.session_id = session.id
                    AND reponse_prenom.question_id = 3
                INNER JOIN reponse AS choix_formation
                    ON choix_formation.session_id = session.id
                    AND choix_formation.question_id = 14
                INNER JOIN choix
                    ON choix_formation.choix_id = choix.id
        """, conn)
    rows = cur.fetchall()
    cur.close()

    df = pd.DataFrame(rows)
    nom_formation = df.loc[:, 4].unique()  # récupère la colonne formation
    df["nom_prenom"] = df[1] + " " + df[2]  # concatène la colonne nom et prénom en une nouvelle colonne
    nom_etudiant = df.loc[:, "nom_prenom"]  # récupère la colonne concaténé précédement
    date_dataframe = df.loc[:, 5].unique()  # récupère la date

    if request.method == "POST":
        retour_html_date = request.json['date']

        cur = conn.cursor()
        # Requête SQL pour récupérer les noms de formations par rapport à la date choisi.
        cur.execute("""SELECT DISTINCT choix.libelle, choix.id
                    FROM choix
                    inner join reponse on choix_id = choix.id
                    inner join session on session.id = reponse.session_id
                    where reponse.question_id = 14
                    AND YEAR(session.date) = %s
                    """, (retour_html_date,))
        affichage_formation = cur.fetchall()
        nom_colonne = [x[0] for x in cur.description]
        cur.close()

        nom_formation_dictionnaire = []
        for row in affichage_formation:
            nom_formation_dictionnaire.append(dict(zip(nom_colonne, row)))
        return jsonify(nom_formation_dictionnaire)

    return render_template("formulaire_pedag.html", formation=nom_formation, etudiant=nom_etudiant,
                           date_dataframe=date_dataframe)


@app.route('/api/etudiant', methods=['POST'])
def liste_etudiant():
    """
    Name: liste_etudiant
    Objet: Permet de traiter l'affichage des étudiants dans le select
    :return: Renvoi un dictionnaire au format JSON pour traitement en Javascript
    """
    conn = get_db()
    cur = conn.cursor()
    retour_html_formation = request.json['formation']  # récupère le nom de la formation du formulaire de "/"
    retour_html_date = request.json['date']  # récupère la date de la formation du formulaire de "/"
    # Requête SQL qui récupère la liste des étudiants selons "retour_html_formation" et "retour_html_date"
    cur.execute("""SELECT session.id,
                    reponse_nom.texte AS Nom,
                    reponse_prenom.texte AS Prenom
                    FROM session
                    INNER JOIN reponse AS reponse_nom
                    ON reponse_nom.session_id = session.id
                    AND reponse_nom.question_id = 2
                    INNER JOIN reponse AS reponse_prenom
                    ON reponse_prenom.session_id = session.id
                    AND reponse_prenom.question_id = 3
                    INNER JOIN reponse AS choix_formation
                   ON choix_formation.session_id = session.id
                    AND choix_formation.question_id = 14
                    AND choix_formation.choix_id = %s
                    AND YEAR(session.date) = %s
                    """, (retour_html_formation, retour_html_date))
    affichage_etudiant = cur.fetchall()
    nom_colonne = [x[0] for x in cur.description]
    cur.close()

    nom_etudiant_dictionnaire = []
    for row in affichage_etudiant:
        nom_etudiant_dictionnaire.append(dict(zip(nom_colonne, row)))
    return jsonify(nom_etudiant_dictionnaire)


@app.route('/api/all', methods=['POST'])
def liste_all():
    """
    Name: liste_all
    Objet: Récupère la liste de tout les étudiants si aucun filtre n'est appliqué
    :return: Renvoi un dictionnaire au format JSON pour traitement en Javascript
    """
    conn = get_db()
    cur = conn.cursor()
    retour_html_date = request.json['date']
    # Requête SQL pour récupérer la liste de tout les étudiants
    cur.execute("""SELECT
                    reponse_nom.texte AS Nom,
                    reponse_prenom.texte AS Prenom
                    FROM session
                    INNER JOIN reponse AS reponse_nom
                        ON reponse_nom.session_id = session.id
                        AND reponse_nom.question_id = 2
                     INNER JOIN reponse AS reponse_prenom
                        ON reponse_prenom.session_id = session.id
                        AND reponse_prenom.question_id = 3;
                    """, retour_html_date)
    affichage_all = cur.fetchall()
    nom_colonne = [x[0] for x in cur.description]
    cur.close()

    nom_etudiant_dictionnaire = []
    for row in affichage_all:
        nom_etudiant_dictionnaire.append(dict(zip(nom_colonne, row)))
    return jsonify(nom_etudiant_dictionnaire)


@app.route('/tableau', methods=['POST'])
def tableau():
    """
    Name: tableau
    Objet: Affiche un tableau en fonction des filtres utilisé dans '/'.
    Puis propose de choisir une question quantitative pour afficher un graphique.
    :return: Renvoi les colonnes quantitatives ainsi qu'un dictionnaire.
    """
    conn = get_db()
    retour_html_etudiant = request.form.get('etudiant')  # retourne le nom de l'étudiant
    retour_html_formation = request.form.get('formation')  # retourne le nom de la formation

    if retour_html_etudiant != "" and retour_html_etudiant is not None:
        # Requête SQL pour récupérer les questions selon le nom et prénom de l'étudiant
        tableau = pd.read_sql("""
                                SELECT session.id  ,concat(lpad(question.id,3,'0')," ",question.libelle) as question, 
                                reponse.texte, reponse.date, reponse.score from reponse

                                inner join question on question.id = reponse.question_id
                                inner join session on session.id = reponse.session_id

                                WHERE session.id in (select session.id FROM session

                                INNER JOIN reponse AS reponse_nom
                                ON reponse_nom.session_id = session.id
                                AND reponse_nom.question_id = 2
                                INNER JOIN reponse AS reponse_prenom
                                ON reponse_prenom.session_id = session.id
                                AND reponse_prenom.question_id = 3

                                WHERE concat(reponse_nom.texte," " ,reponse_prenom.texte)= %s) """

                              , conn, params=(retour_html_etudiant,))

        # Requête SQL pour récupérer la liste des questions quantitatives par rapport à l'étudiant
        tab_score2 = pd.read_sql(""" SELECT session.id ,question.libelle as question, reponse.score as score from reponse
                                                     inner join question on question.id = reponse.question_id
                                                     inner join session on session.id = reponse.session_id

                                                     WHERE  score is not null and session.id in (select session.id FROM session

                                                    INNER JOIN reponse AS reponse_nom
                                                    ON reponse_nom.session_id = session.id
                                                    AND reponse_nom.question_id = 2
                                                    INNER JOIN reponse AS reponse_prenom
                                                    ON reponse_prenom.session_id = session.id
                                                    AND reponse_prenom.question_id = 3

                                                    WHERE concat(reponse_nom.texte," " ,reponse_prenom.texte)= %s)
                                                      """, conn, params=(retour_html_etudiant,))

    elif retour_html_formation != "":
        # Requête SQL pour recupérer tout les etudiants de la formation
        tableau = pd.read_sql("""
                                SELECT session.id  ,concat(lpad(question.id,3,'0')," ",question.libelle) as question, 
                                reponse.texte, reponse.date, reponse.score from reponse

                                inner join question on question.id = reponse.question_id
                                inner join session on session.id = reponse.session_id

                                WHERE session.id in (SELECT DISTINCT session.id FROM session 

                                inner join reponse on session.id = reponse.session_id
                                where reponse.question_id = 14
                                AND reponse.choix_id= %s) """

                              , conn, params=(retour_html_formation,))

        # Requête SQL pour récupérer la liste des questions quantitatives par rapport à la formation
        tab_score2 = pd.read_sql(""" SELECT session.id ,question.libelle as question, reponse.score as score from reponse
                                                            inner join question on question.id = reponse.question_id
                                                            inner join session on session.id = reponse.session_id

                                                            WHERE  score is not null 
                                                            AND session.id in (SELECT DISTINCT session.id FROM session 

                                                            inner join reponse on session.id = reponse.session_id
                                                            where reponse.question_id = 14
                                                            AND reponse.choix_id= %s)
                                                             """, conn, params=(retour_html_formation,))

    else:
        # Requête SQL pour recupérer tout les etudiants toute promotion confondu
        tableau = pd.read_sql("""
                                SELECT session.id  ,concat(lpad(question.id,3,'0')," ",question.libelle) as question, 
                                reponse.texte, reponse.date, reponse.score from reponse

                                inner join question on question.id = reponse.question_id
                                inner join session on session.id = reponse.session_id""", conn)

        # Requête SQL pour récupérer la liste des questions quantitatives
        tab_score = pd.read_sql(""" SELECT session.id ,question.libelle as question, reponse.score as score from reponse
                                                         inner join question on question.id = reponse.question_id
                                                         inner join session on session.id = reponse.session_id

                                                          where score is not null
                                                          ;""", conn)

    try:
        tableau['date'] = tableau['date'].dt.strftime('%Y-%m-%d')  # change le format de la date vers un string

    except AttributeError:
        print("Pas de date à formater")

    # concatène les colonnes entre elles pour ne plus avoir de valeur vide
    b = tableau['texte'].fillna(tableau['score']).fillna(tableau["date"])
    tableau["reponse"] = b

    # Pivote 'tableau' pour avoir les questions en colonnes
    a = pd.DataFrame.pivot(tableau, index="id", columns="question", values="reponse")
    a_dict = a.to_dict(orient="records")

    # Pivote 'tab_score' pour avoir les questions en colonnes
    tab_score_pivot = pd.DataFrame.pivot(tab_score2, index="id", columns="question", values="score")
    colonnes = tab_score_pivot.columns

    return render_template("tableau.html", tab=a_dict, colonnes=colonnes, nom_formation=retour_html_formation)


@app.route('/api/tab', methods=['POST'])
def api_tab():
    """
    Name: api_tab
    Objet: Permet le traitement de l'affichage du graphique pour les questions quantitatives.
    :return: Renvoi un JSON de la figure, afin de l'afficher dans la route '/tableau'.
    """
    nom_formation = request.json["nom_formation"]
    conn = get_db()
    # Requête SQL pour récupérer la liste des questions quantitatives
    tab_score = pd.read_sql(""" SELECT session.id ,question.libelle as question, reponse.score as score from reponse
                                                 inner join question on question.id = reponse.question_id
                                                 inner join session on session.id = reponse.session_id

                                                  where score is not null and session.id in 
                                                 (SELECT DISTINCT session.id FROM session 

                                                    inner join reponse on session.id = reponse.session_id
                                                    where reponse.question_id = 14
                                                    AND reponse.choix_id= %s)



                                                  ;""", conn, params=(nom_formation,))

    # Pivote 'tab_score' pour avoir les questions en colonnes
    tab_score_pivot = pd.DataFrame.pivot(tab_score, index="id", columns="question", values="score")

    question_quant = request.json["question_quant"]  # Récupère la question choisi dans '/tableau'
    fig = px.histogram(tab_score_pivot, x=question_quant, histnorm="percent",
                       barmode='relative', nbins=8)
    figure = to_json(fig)
    return figure


if __name__ == '__main__':
    app.run()
