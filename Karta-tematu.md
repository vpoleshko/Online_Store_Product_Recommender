# Karta zgłoszenia tematu projektu

**Grupa:** L2 · **Zespół:** "Nr 1 - "Smoki":  Antoni Przyłuski, Volodymyr Poleshko, Arsenii Voron · **Data:** 22.10.2026
Sztuczna inteligencja — laboratorium · Collegium Da Vinci · rok akad. 2026/2027
Oddajecie mailem do **22.10, 16:45**, temat `SI L2 · Z<nr zespołu> · karta`.

## 1. Skład zespołu

> Rola jest wstępna — można ją zmienić w trakcie projektu bez uzgadniania.

| Imię i nazwisko | Nr albumu | Rola (wstępna) |
|---|---|---|
| Antoni Przyłuski|31129 | Frontend / UX|
| Volodymyr Poleshko|31078 | Data Scientist, Project Manager | 
| Arseni Voron|31818 | Backend, Developer |

## 2. Roboczy tytuł (PL)
System rekomendacji produktów w sklepie internetowym
## 3. Tytuł (EN)
Product recommendation system in an online store
## 4. Problem — co system ma robić i dla kogo (3–5 zdań)
Podczas poszukiwania zakupów online często podczas wyszukiwania dokładnej rzeczy pojawiają się rzeczy kompletnie nie związane z kryteriami naszego wyszukiwania. Ten system ma zapamiętywac poprzednie nasze wybory i na podstawie historii wyszukiwania i podpowiadanych przez sam system artykułów podobnych do naszego wyszukiwania rekomenduje odpowiednie rzeczy Odniesienie: Problematyczne wyszukiwanie i problem z rekomendacją stron zakupowych
## 5. Technologia SI

- [ ] sieć neuronowa
- [ ] system ekspertowy / wnioskowanie regułowe
- [ ] algorytm genetyczny
- [x] klasyczne uczenie maszynowe

Algorytm będzie analizował historię zakupów i podobieństwo między produktami. Na tej podstawie system będzie rekomendował użytkownikowi produkty podobne do tych, które kupował wcześniej. ( Item-based Collaborative Filtering z wykorzystaniem.) ( KNN ) scikit-learn

Dlaczego ta technologia pasuje do tego problemu (2–3 zdania):

Ponieważ przeważnie tego typu historie wyszukiwania i rekomendacje używają uczenia maszynowego jako fundament sprawdzania 
czego użytkownik szuka i na podstawie historii przeglądania podawać przykładowe wyniki. Uczenie maszynowe w porównaniu
do innych wyborów nie wymaga dużych zasobów pamięci i ilości danych i działa szybko, zwracając uwagę na to że
użytkownik nie będzie cały dzień siedział przed serwisem sklepu.

## 6. Dane

- Źródło: Retailrocket Recommender System Dataset — publiczny zbiór danych dostępny na platformie Kaggle, zawierający historię interakcji użytkowników z produktami w sklepie internetowym.
  
- Rozmiar / format: Pliki CSV zawierające informacje o przeglądaniu produktów, dodawaniu ich do koszyka, zakupach oraz właściwościach produktów.
  
- Czy dane są już dostępne? Tak — zbiór danych jest dostępny na Kaggle. Plan pozyskania: pobranie plików CSV, przygotowanie danych w Pythonie i import do bazy danych MongoDB.

## 7. Stos technologiczny

Warstaw uczenia maszynowego
Warstwa Backendu / API
Baza Danych
Warstwa Frontendu / Interfejsu

Python, pandas, numpy, scikit-learn,  matplotlib

## 8. Kryterium sukcesu

- Metryka i próg: ilośc wybranych produktów pasujących do historii wyszukiwania, top najlepszych do tego pasujących zwróconych przez system
- Punkt odniesienia (prosta metoda, z którą porównacie wynik): Klasyczne wyszukiwanie słów kluczowych, wybrane produkty np. z Bazy danych sql plecenia
LIKE

Metryka: Precision@5 - to metryka, która pokazuje, ile spośród pięciu rekomendowanych produktów jest trafnych. Będziemy porównywać rekomendacje systemu z rzeczywistymi zakupami użytkowników. Dzięki temu sprawdzimy skuteczność naszego algorytmu.

Próg sukcesu: Precision@5 ≥ 10%.

System będzie generował 5-8 rekomendowanych produktów dla użytkownika. Sprawdzimy, ile z nich faktycznie znalazło się w jego późniejszych zakupach.

Punkt odniesienia: Prosty system rekomendujący najpopularniejsze produkty. Nasz algorytm powinien osiągać lepszy wynik niż ta metoda.

Jeśli użytkownik nie ma jeszcze historii zakupów, przed dokonaniem pierwszego zakupu wypełni krótką ankietę, w której zadamy mu kilka pytań dotyczących jego zainteresowań i preferencji. Dzięki temu system będzie mógł lepiej zrozumieć, czego użytkownik szuka, i zaproponować mu odpowiednie produkty.

Gdy użytkownik zacznie dokonywać zakupów, system będzie analizował jego historię zakupową i na jej podstawie stopniowo ulepszał rekomendacje, aby były bardziej trafne i dostosowane do jego potrzeb.

## 9. Zakres minimalny (co powstanie na pewno)

system uczący się na historii wybieranych rzeczy i przedstawiający najbardziej trafne / podobne do naszego wyszukiwania

## 10. Zakres opcjonalny (co dorobimy, jeśli starczy czasu)

Pełna strona sklepu, graficznie i logicznie działająca

## 11. Repozytorium

https://github.com/vpoleshko/Online_Store_Product_Recommender/edit/main/

## 12. Główne ryzyko i plan awaryjn

**Główne ryzyko:** Zbyt mała liczba zakupów niektórych użytkowników oraz niska skuteczność rekomendacji.

**Plan awaryjny:** Jeśli algorytm KNN nie osiągnie wymaganej skuteczności, zastosujemy prostszy system rekomendacji oparty na najpopularniejszych produktach. Dla użytkowników bez historii zakupów albo bez uzypewnego formularza również będziemy wyświetlać najpopularniejsze produkty.

Dzięki temu system będzie działał nawet przy niewystarczającej ilości danych.
plan awarynjy: wybranie innego, prostszego rozwiązania
*Decyzja prowadzącego:* [ ] zatwierdzony  [ ] do poprawy · *Uwagi:*


