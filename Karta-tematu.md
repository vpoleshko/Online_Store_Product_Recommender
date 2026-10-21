# Karta zgłoszenia tematu projektu

**Grupa:** L2 · **Zespół:** Antoni Przyłuski, Volodymyr Poleshko, Arsenii Voron · **Data:** 22.10.2026
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

Dlaczego ta technologia pasuje do tego problemu (2–3 zdania):

Ponieważ przeważnie tego typu historie wyszukiwania i rekomendacje używają uczenia maszynowego jako fundament sprawdzania 
czego użytkownik szuka i na podstawie historii przeglądania podawać przykładowe wyniki. Uczenie maszynowe w porównaniu
do innych wyborów nie wymaga dużych zasobów pamięci i ilości danych i działa szybko, zwracając uwagę na to że
użytkownik nie będzie cały dzień siedział przed serwisem sklepu.

## 6. Dane

- Źródło: Przykładowe strony do wykonywania zakupów, źródła o uczeniu maszynowym
- Rozmiar / format: CVS / JSON
- Czy dane są już dostępne? tak / nie — plan pozyskania: jeszcze nie

## 7. Stos technologiczny

Warstaw uczenia maszynowego
Warstwa Backendu / API
Baza Danych
Warstwa Frontendu / Interfejsu

## 8. Kryterium sukcesu

- Metryka i próg: ilośc wybranych produktów pasujących do historii wyszukiwania, top najlepszych do tego pasujących zwróconych przez system
- Punkt odniesienia (prosta metoda, z którą porównacie wynik): Klasyczne wyszukiwanie słów kluczowych, wybrane produkty np. z Bazy danych sql plecenia
LIKE

## 9. Zakres minimalny (co powstanie na pewno)

system uczący się na historii wybieranych rzeczy i przedstawiający najbardziej trafne / podobne do naszego wyszukiwania

## 10. Zakres opcjonalny (co dorobimy, jeśli starczy czasu)

Pełna strona sklepu, graficznie i logicznie działająca

## 11. Repozytorium

(uzupełnicie 22.10)

## 12. Główne ryzyko i plan awaryjny
ryzyko: zbyt uboga historia wyszukiwania i działania systemu, niedokładnie działający system rekomendacji
---
plan awarynjy: wybranie innego, prostszego rozwiązania
*Decyzja prowadzącego:* [ ] zatwierdzony  [ ] do poprawy · *Uwagi:*
