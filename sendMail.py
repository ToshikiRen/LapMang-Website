import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random

letterBank = 'qwertyuioplkjhgfdsazxcvbnmQWERTYUIOPLKJHGFDSAZXCVBNM1234567890!#$%^&*(){}:"|?><'

def generateSecretKey():

    global letterBank
    secretKey = ''
    for i in range(10):
        secretKey += letterBank[random.randint(0, len(letterBank))]
    
    return secretKey


def sendEmail(secretKey, receiver_email):
    sender_email = "proiectBazeDeDate@gmail.com"
    password = 'tpyfurmyykyocmpe'

    message = MIMEMultipart("alternative")
    message["Subject"] = "Cod unic inregistrare"
    message["From"] = sender_email
    message["To"] = receiver_email

    # Text simplu + HTML
    text = """\
    Buna ziua,
    
    Aveti atasat mai jos codul unic necesar finalizarii inregistrarii

    Cod Unic """ + str(secretKey)
    
    html = """\
    <html>
    <body>
        <p>Buna ziua,<br>
        Aveti atasat mai jos codul unic necesar finalizarii inregistrarii<br>
        <br>
        Cod Unic: """ + str(secretKey) +    """
        </p>
    </body>
    </html>
    """



    # Transformare in obiecte de tip  MIMEText
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Adaugare mesaje, clientul o sa incerce prima data
    # sa incarce mesajul "part2"
    message.attach(part1)
    message.attach(part2)

    # Securizarea conexiunii
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(
            sender_email, receiver_email, message.as_string()
        )

