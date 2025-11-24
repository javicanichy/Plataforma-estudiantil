from servidorBackend import app, db
from models import Noticia
from datetime import datetime

with app.app_context():
    noticia = Noticia(
        titulo="Curso de Simulación Clínica",
        contenido="""
        <p>Este evento ha tenido lugar en la Facultad de Ciencias de la Salud, en el Anfiteatro. 
        En la apertura pudimos contar con la presencia del Vicerrector <strong>Crissantos Asumu</strong>, 
        el Decano <strong>Bismar Hernández Reyes</strong> y la Vice Decana <strong>María Flora Esono Nchama</strong>.</p>

        <p>Dicho evento tuvo una duración de tres días, del <strong>18 al 20 de noviembre 2025</strong>, en horario de <strong>8:15 a 9:45 h</strong>. 
        Los facilitadores españoles hicieron énfasis en los primeros pasos a realizar cuando un paciente se encuentra en una situación de vida o muerte.</p>
        """,
        fecha=datetime(2025, 11, 20).date(),
        imagen="noticias2.jpg",
        pie_foto="Curso de simulación clínica – Anfiteatro Facultad",
        enlace_programa="/mnt/data/e2adec70-3d2b-4e15-a1b7-7d023b59e58b.png"
    )
    db.session.add(noticia)
    db.session.commit()
    print("✅ Noticia insertada correctamente")
