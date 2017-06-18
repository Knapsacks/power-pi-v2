import json
override=json.loads(open('override.json').read())[0]['override']
while True:
    o=input("Wanna Override ? (YES or NO)").split()[0]
    if o.lower()=="yes":
        with open('override.json', 'w') as outfile:
            json.dump(json.loads('[{"override":"1"}]'), outfile)
    else:
        with open('override.json', 'w') as outfile:
            json.dump(json.loads('[{"override":"0"}]'), outfile)
