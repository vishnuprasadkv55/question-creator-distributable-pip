


import os
import re
import base64

def createHtmlString(text, class_name):
    htmlStyring = ""
    entityKeys = []
    # firstPath = os.getcwd() + '\Sent\Sent\img'
    firstPath = 'https://raw.githubusercontent.com/vishnuprasadkv55/question-bank/master/data_1/img'
    obj = 'image'
    #with extensions
    # text = "This is a sample [[image:image1]] to show how [[image:image2]] can be held.[[vedio:vedio1]]"
    entites = re.findall(r"\[\[\[\s(.*?)\s]]]" , str(text))
    for item in entites:
        if obj=='image':
            # encoded = base64.b64encode(open(firstPath + '\\' + item, "rb").read())
            # decoded = 'data:image/png;base64,{}'.format(encoded.decode())
            text = text.replace('[[[ '+item+' ]]]','<Image' +' class='+ class_name +' src=' + firstPath + '/' + item +' />')
            entityKeys.append(firstPath+'/' + item)
        if obj=='vedio':
            #dummy vedio poster image
            text = text.replace('[['+item+']]','<Player playsInline poster="vedioposter.png" src='+firstPath+'/' + item +' />')
            entityKeys.append(firstPath+'/' + item)
    return text