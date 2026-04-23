# GUIA OO para Iniciantes

Este guia explica o projeto como se fosse sua primeira experiência com orientação a objetos.

## 1) Como pensar em OO aqui

No estilo procedural, normalmente fazemos várias funções e chamamos em sequência.
Em OO, agrupamos comportamentos por responsabilidade:

- classe de download cuida de internet;
- classe de limpeza cuida de texto;
- classe de frequência cuida de cálculo;
- classe de repositório cuida do CSV;
- classe comparadora cuida da matemática;
- classe serviço coordena tudo.

## 2) Mapeamento: versão funcional -> versão OO

- `baixar_texto(...)` -> `TextDownloader.download(...)`
- `limpar_texto(...)` -> `TextCleaner.clean(...)`
- `calcular_frequencia(...)` -> `FrequencyCalculator.compute(...)`
- `carregar_perfis_csv(...)` -> `LanguageProfileRepository.load(...)`
- `comparar_perfis(...)` -> `LanguageComparator.compare(...)`

## 3) Fluxo completo do programa

1. CLI lê os argumentos.
2. CLI cria um `AppConfig`.
3. CLI monta as classes e cria `LanguageIdentifierService`.
4. Serviço chama:
   - downloader
   - cleaner
   - frequency calculator
   - repository
   - comparator
5. Serviço retorna `IdentificationResult`.
6. CLI imprime o idioma final e o ranking.

## 4) Por que isso ajuda

- Código fica mais organizado para times.
- Testes ficam mais simples porque podemos testar uma classe por vez.
- Evolução futura é mais segura (trocar implementação sem quebrar tudo).

## 5) Exemplo mental de composição

Pense no `LanguageIdentifierService` como um "maestro".
Ele não toca todos os instrumentos: ele coordena quem toca cada parte.
Cada classe especializada faz seu papel, e o resultado final surge da colaboração.
