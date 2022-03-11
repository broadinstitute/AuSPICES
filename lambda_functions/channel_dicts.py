def find_map(dictionary_name):
    if dictionary_name == "Standard_1BF":
        map = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield": "OrigBrightfield",
        }

    elif dictionary_name == "Standard_1BF_V":
        map = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield CP": "OrigBrightfield",
        }

    elif dictionary_name == "Standard_3BF":
        map = {
            "HOECHST 33342": "OrigDNA",
            "Alexa 568": "OrigAGP",
            "Alexa 647": "OrigMito",
            "Alexa 488": "OrigER",
            "488 long": "OrigRNA",
            "Brightfield": "OrigBrightfield",
            "Brightfield H": "OrigBrightfield_H",
            "Brightfield L": "OrigBrightfield_L",
        }
    else:
        map = False
    return map
