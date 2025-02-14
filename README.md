# RateIt  

## Opis projekta  
RateIt je web aplikacija koja korisnicima omogućuje dijeljenje recenzija i ocjena proizvoda. 
Cilj aplikacije je stvoriti zajednicu u kojoj korisnici mogu razmjenjivati svoja iskustva o različitim proizvodima, pomažući jedni drugima u donošenju informiranih odluka prilikom kupnje. 
Aplikacija omogućava dodavanje recenzija, pretraživanje proizvoda prema kategorijama i ocjenama, te interakciju među korisnicima putem komentara i ocjena recenzija. 
Svaki korisnik ima svoj profil u kojem može pratiti svoje aktivnosti i omiljene proizvode. 
Za razvoj aplikacije korišten je Python za backend, koristeći FastAPI za izradu REST API-ja. 
Aplikacija je kontejnerizirana uz pomoć Docker-a. Podaci su pohranjeni u AWS DynamoDB. Također, korišten je AWS S3 za pohranu datoteka, a autentifikacija korisnika se provodi pomoću JWT.

## Tehnologije  
- **Backend**: Python (FastAPI)  
- **Baza podataka**: AWS DynamoDB  
- **Pohrana datoteka**: AWS S3  
- **Autentifikacija**: JWT  
- **Kontejnerizacija**: Docker & Docker Compose  

## Struktura sustava  
Aplikacija je podijeljena u tri servisa:  
- **Auth Service** – registracija, prijava i verifikacija korisnika  
- **User Service** – upravljanje korisnicima i omiljenim proizvodima  
- **Review Service** – dodavanje, uređivanje i pregled recenzija  

## Zaključak  
RateIt omogućuje jednostavno dijeljenje recenzija i pomaže korisnicima u odabiru najboljih proizvoda.  
