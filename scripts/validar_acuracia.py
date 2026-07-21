# Salve como verificar_acuracia.py e execute com: python verificar_acuracia.py
import json
import os

print('📊 ACURÁCIAS REAIS (arquivos JSON):\n')

for arquivo in sorted(os.listdir('data/verificacoes')):
    if arquivo.endswith('.json'):
        moeda = arquivo.replace('.json', '')
        with open(f'data/verificacoes/{arquivo}') as f:
            dados = json.load(f)
        
        print(f'💰 {moeda}:')
        
        for h in ['5', '15', '30', '60', '300', '900', '1800', '3600']:
            if h in dados:
                d = dados[h]
                total = d.get('total', 0)
                acertos = d.get('acertos', 0)
                if total > 0:
                    acc = acertos / total * 100
                    barra = '█' * int(acc/10) + '░' * (10 - int(acc/10))
                    print(f'  {h}s: {barra} {acc:.1f}% ({acertos}/{total})')
        print()