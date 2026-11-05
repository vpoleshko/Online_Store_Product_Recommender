# Karta zgłoszenia tematu projektu

**Grupa:** L2 · **Zespół:** "Nr 1 - "Smoki":  Antoni Przyłuski, Volodymyr Poleshko, Arsenii Voron · **Data:** 22.10.2026
Sztuczna inteligencja — laboratorium · Collegium Da Vinci · rok akad. 2026/2027
Oddajecie mailem do **22.10, 16:45**, temat `SI L2 · Z<nr zespołu> · karta`.

## 1. Skład zespołu

> Rola jest wstępna — można ją zmienić w trakcie projektu bez uzgadniania.

| Imię i nazwisko | Nr albumu | Rola (wstępna) |
|---|---|---|
| Antoni Przyłuski|31129 | Data Scientist, Project Manager |
| Volodymyr Poleshko|31078 | Frontend / UX | 
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

Algorytm będzie analizował historię zakupów i podobieństwo między produktami. Na tej podstawie system będzie rekomendował użytkownikowi produkty podobne do tych, które kupował wcześniej. ( Item-based Collaborative Filtering z wykorzystaniem.) ( KNN )

Dlaczego ta technologia pasuje do tego problemu (2–3 zdania):

Ponieważ przeważnie tego typu historie wyszukiwania i rekomendacje używają uczenia maszynowego jako fundament sprawdzania 
czego użytkownik szuka i na podstawie historii przeglądania podawać przykładowe wyniki. Uczenie maszynowe w porównaniu
do innych wyborów nie wymaga dużych zasobów pamięci i ilości danych i działa szybko, zwracając uwagę na to że
użytkownik nie będzie cały dzień siedział przed serwisem sklepu.

## 6. Dane

- Źródło: Retailrocket Recommender System Dataset — publiczny zbiór danych dostępny na platformie Kaggle, zawierający historię interakcji użytkowników z produktami w sklepie internetowym.
  
- Rozmiar / format: Około 305 MB (plik ZIP po pobraniu), format CSV. Zbiór zawiera około 2,75 mln zdarzeń użytkowników, m.in. przeglądanie produktów, dodawanie do koszyka i zakupy.
  
- Czy dane są już dostępne? Tak

## 7. Stos technologiczny

Python 3.10+, Postgresql,
pandas, numpy, scikit-learn, matplotlib, nootebook, docker, react, JavaScript, CSS, FAST API

## 8. Kryterium sukcesu

**Metryka główna:** **Precision\@5** – określa, ile spośród pięciu rekomendowanych produktów odpowiada późniejszym zakupom użytkownika.

**Próg sukcesu:** Precision\@5 ≥ 10%.

**Metryka porównawcza:** Macro-F1\@5 – średnia wartość F1\@5 obliczona dla wszystkich ocenianych użytkowników.

**Punkt odniesienia (Baseline):** Prosty algorytm rekomendujący najpopularniejsze produkty (Top Popular Products), niewykorzystujący uczenia maszynowego.

**Dodatkowy próg sukcesu:** Model Item-based KNN z mechanizmem Popularity Fallback powinien osiągnąć Macro-F1\@5 wyższe od Baseline o co najmniej 0,005.

**Macro-F1\@5(KNN) − Macro-F1\@5(Baseline) ≥ 0,005**

**Wstępne wyniki porównania:**

| Metryka      | Baseline | KNN + Fallback |
| ------------ | -------- | -------------- |
| Precision\@5 | 0,0045   | 0,0102         |
| Macro-F1\@5  | 0,0054   | 0,0122         |

Liczba ocenianych użytkowników: **353**.

**Uzyskana poprawa Macro-F1@5 wynosi +0,0068 (około 126%) względem Baseline.** Dodatkowy próg został spełniony we wstępnych testach, natomiast główny próg Precision@5 ≥ 10% nie został jeszcze osiągnięty.

**Rekomendacje dla nowych użytkowników:** Jeśli użytkownik nie ma historii zakupów, wypełni krótką ankietę dotyczącą swoich zainteresowań i preferencji. Wraz z pojawianiem się kolejnych zakupów system będzie analizował historię użytkownika i dostosowywał rekomendacje.

**Zobowiązanie zespołu:** Zobowiązujemy się do dalszego doskonalenia modelu oraz potwierdzenia wyników na niezależnym zbiorze testowym.


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


