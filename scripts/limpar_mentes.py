import json

# Carrega
d = json.load(open('data/minds.json'))

# Pega IDs das moedas
from Software.core.universe_instance import universo
ids_moedas = []
for app in universo.apps:
    if hasattr(app, 'nome') and app.nome == 'crypto_app':
        for moeda, id_dado in app.ids_cripto.items():
            ids_moedas.append(str(id_dado))
        break

print(f'IDs das moedas: {ids_moedas}')

# Mantém só as moedas
antes = len(d['mentes'])
d['mentes'] = {k: v for k, v in d['mentes'].items() if k in ids_moedas}
depois = len(d['mentes'])

# Salva
json.dump(d, open('data/minds.json', 'w'), indent=2)
print(f'Mentes: {antes} → {depois} (removidas {antes - depois})')