import re

doctor_list_raw = """
Dr ABOUSSOU STEPHANE
Dr KOUROUMA WASSIRIKI
Dr KRABOU SIDNEY
Dr DOSSO AICHA
Dr OUATTARA YAYA
Dr INAGO CEDRIC
Dr LOKOU ADJOH
Dr N'KON KOUAME
Dr YAF KRA KOFFI
Dr ASSI BRICE
Dr ASSOUMA RITA
Dr TRAORE MEDE
Dr TOUALY MADOCHE
Dr TANOE ROSE
Dr GNOUHOUR YAHE
Dr MELEDJE GRACE
Dr ALEGRA ABRAKON
Dr AMON SIDONIE
Dr OGOU VALENTIN
Dr DJOUMAN AUDREY
Dr DONGO KOUAME
Dr AMON ANGE
IDE KOFFIF KOUAME
Dr KOUAKOU ESTELLRE
Dr TAH BI JULES
Dr BAMBA MALIKA
Dr N'GUESSAN DIARASSOUBA
Dr KOUADIO BAISSA
Dr N'ZI YAO
Dr KABORE GEDEON
Dr AHONON RICHARD
Dr AMANI ANZIAN
Dr ASSANDE GUILLAUME
IDE TCHOUMOU NATALIE
IDE EBONI EZECKIEL
Dr YAO YANN
Dr MANGOUA PAUL
Dr KONAN LUC
Dr BILE EKRA
Dr JACQUES KOUAKOU
SF BOKA Epse KOUAME
Dr KOUAME STEPHANE
Dr KOUSSAN FRANCOIS
Dr AWA ATTE
Dr ASSI ANGBA BRICE
Dr EDI BOFFOU
IDE GBEGOU MOIEL
Dr KPEA IVAN CEDRIC
Dr KOUASSI KOFFI
Dr MENOIT GREGOIRE
Dr KOUASSI NHEL
Dr GILE MOHAMED
SF BELLOU ARIANE
IDE AKA TANDJI HONORE
Dr KONDJI K. OZEH
Dr KONAN JOACHIN
Dr OUATTARA EL YATA
Dr BAH GRAH GYRI
IDE KOUADIO SERGE
Dr MENOIT MAHI DOUGLAS
Dr KOUAME CLAVER
IDE AKA JEAN RENE
IDE YOBOU epse ADDN
SF AKE ROSANI
SF DIALLO Née KOUAME
SF SONAN ANDRE H
Dr FENI ROSINI
Dr BILE BERTRAND
Dr BAH LUCIEN
Dr DOHI BI GOA L
Dr KONE ADAMA
Dr KOUAKOU GINETE
Dr N'GUESSAN K. ETIENNE
IDE KONE DRAMANE
Dr KPEL N'GUESSAN
Dr MFOUMANE DOUGLAS
IDE SOUMAHORO LASSINA
IDE KOUASSI GNANGRE
Dr ODEHE ANNICK
Dr ALLEGRA ABRAHAM
SF TRAORE BIN TOU
Dr ALLO BOU
SF BOKA Epse KOUAME
Dr VEDGOUNOU ROMEO
IDE ANOMA ELISABETH
IDE KOUAME AHOU A.
SF YAO née BROU AKISSI
SF DIALLO Née SANFO
Dr YEO KPOUNOU ASSITA
Dr NARCISSE KOUADIO
Dr KOFFI KOUASSI KANI
Dr DIAGRA OFELA I.
Dr KOFFI PARFAIT
Dr GNAHORE DAVID
Dr MENOIT GREGOIRE H.
Dr AHEBROU F.
IDE AMIAN BEATRICE
Dr KOUAKOU YAH
ACHO ROMEO
Dr AKA PASCAL
Dr KASSI CHRISTOPHE
Dr KOFFI AYA ROSINE F.
SF EDI MARIE
SF KOFFI Née KOUADJO
SF SANOGO Née DIARRASO
SF KOFFI Née DJAKANA
IDE HOUEGNON RODRIGUE
Dr YAO KOUAKOU
Dr N'GUESSAN HELENE
IDE YAO HELENE
Dr GAUZE JEAN CLAUDE
IDE YAO KOUADIO ALFRED
Dr N'DA TOTHU D. N.
IDE AKOTO GUIA M.
Dr YAO KOFFI MATHURIN
Dr CISSE FATIMATA
IDE TENI ANGELIQUE
Dr AMATA ERIC
Dr GOUESSE Y. PATRICE
Dr KPELE YABA B.
Koffi Didier
Touré taha épouse kouamé
Adjouman Hervé
Balou Diop
Botti Lou Nédège
N'guessan Valerie
Esnel Franck
Diallou Gérald
Bodel Parfait
Bodel Hyacinthe
Bawar Firmin
Abdallah Becoüé
Kone Ibrahim
Allimi Lawal
Kto Eugénie
Bansanon fortune
Ného Moise
Bami Ismaél
Niho Marie
Yacine Malick
Agbo Niam Nazaire
Diomandé Katienou
Gnankey Venise
N'Dri
Douzoua Marc
Mc Amalo
Tano Simon
N' Taye Seu Nomanto
Akahou Stéphanie
Datamla Koné
Koffi Charles
Gulai Gbaza Adéla
Dimassouba Tchlagban Alassane
Kto Pauline
Kouamé Lou Élodie
Oke
Kochi Thierry Aime
Ette Goulou
Kone Achille
Alassane agiba
Rodrigue Kassi N'guessan
Yapi Eric
Denhe Charles Emmanuel
Kessé Chimène
Kpota Bongo lucis
Kassi Kadjo Martine
Dindji Salomon
N'guessan Guillaume Landry
Méité Alizeta
Zaouli lou Ange
Sikali Aristide
Anka Zéphyrin
Koussi Aman florentine
Wassiou Oro Siriya Oro Wassiou
Barry Ismael
Kra Koudio Honoré
Tiero Kadia Riang
Adballah (0208214603)
Assia Migneli
Djamala Ahou
Assiave Lité
Fadiga Nadia
Beda Jean Alphonse
Bakayoko Haroun
Bodolo Ignace
Digbe Magali
N' MOula Sandrine Jacky
Balo Mireille
Sourakata Camara
Irie Samuel
Kouamé Lou Élodie
Romaric Kouakou
Konin Mialia
Mamadou Coulibaly
Koua Abouli kouakou
Kouacou Anka Adjo
Klaido Odile
Kalogo Arafat
Aboni yves roland koffi
Sanoko facima
Konan bohoussou zene carole
Bahi junior
Kouakou kouadio
Seka Cherif Lacina
Doumbia moussa
Cisse sabary
Kouassi alfred
Kra Idriss ouattara
Kouame infou faustin
Coulibaly timan
Loizoh louame
N'guessan kouame
Gouandeu nicaise
Toure myriam
Julie Romeo
Konan Pacome
Diallo cheick Oumar
kone Sombo
Coulibaly Alilce
Kpasso Marina
Kouakou julien
kessé Chimène
tiada Aminata Touré
Touré pamigean
kassogué marlence
Adja Magboir
ougonou Marina
Sirie Hypolite Fulgence
Bila Arignan Estelle
Quihi Adèle
Adougra Abraham
Kanamoko
Segbeng Hermana
Dené Fatoumata
lapa Evelyne
konan Bénédicte
Diorassouba Aminata
Mr Simon
Quedraogo Layeul
Mamadou Coulibaly
Kouadio Wilfried
Kouakou Sandrine
Alleh Yannick
Bamba Nawa Cheiff
Kouadio louis janvier
AG Eulyone
ZOUE URBAIN
ASSANDE RUNDE
SOUMAHORO SALIMATA
YAYA RIBECA
KOUASSI ZAKOUA
KOUADIO SAMUEL
AGAFOU BERTRAND
GNAGNE VALERIE
BODJI LOUIS
GOZE ANDRE
ABOU FELIX
KOUASSI YAO
AGBEDJE BÉATRICE
JEAN CLAUDE NADO
GOUELI ARISTIDE
DAHIN JEAN
ZAMPOL SILIMANE
PKLE N'GUESSAN
KAKOU AMBROISINE
KOUAME BORIS
ZEDJA GEDEON
NGUESSAN ALPHONSE
TOURE KILOUFOUOH
COULIBALY GNATIOLO
DIOMANDE HAMED
BROU MICHEL
GOGBEU ELYSE
ZAOULI BI ARNAUD
KENGANI ALPHONSE
BENIE N'DA
TOURE BIMAILA
AFFINGEL
KOUMON GHISLAIN
COULIBALY AMINATA
AFFOUMANI DOUGLAS
KONAN ARSENE
OUATTARA
KOUAD ANDERSON
KINIMISSIBO SIKA
FAYE ESSETCHI
GBONA AMBROISE
PAUL MEMEL
AW TIDIANE
BEUGRE ESMEL
VODOUNOU ROMEO
DOH GUY
AGA PATRICK
GNEGA GNABRY
OUATTARA MARIAM
OUFFOUE ROXANNE
SEKONGO NAHOUA
MIME ANOUABA ROME
NEA TIDE
ABO REIJE
BOUSCHOL OUA LABINE
NORO
GNAGNON ROXANNE
NAKAYOKO BIN TOU
ROLAND AMOUYON
YCHIKA ANGE
KOUAKOU AHOU BOSTLINE
WANGBANA AWA
KONE KANAKONON
SALIFOU TEHINI
LOU BI INI
GBEHE TOU ANARETE
AHI N'GESSAN
SEKONGO FATOUMATA
SIAHE GERMAIN
KOUAME MICHAEL
KOUASSI VIVIANE
JULIEN MARCEL
KOUADIO BERNADETTE
BABILE BONIFACE
KOFFI N'DRI
OLIVIER KOUADIO
BASSAN JONAS
N'DRI ALEXANDRE
DOSSO MAMADOU
GOULI CHERIE
IBADO FÉLIX
BADO NOUVOU
WILLY MEMEL
INOTTI PRISCA
WANGRAGUA ABOUBAKAR
YAGUE MARCEL
SAGOU MARIE SOLANGE
TOFANA
ABO YOUSSOUF
EUGENE TANDJI
AKRE PIERRE
SEHME YACOUBA
DODO MARIE JOSEE
SERWE SALIF
ROA KOUASSI
GAMI RI
ZORON CHEICK
CAMARA KARIM
LOBE LILIANE
KOUAME AXELLE
KOFFI ARSÈNE
KONE AICHA
SOKOUA LOUISE
GOUE GONTO BORIS
KONE DRAMANE
GOULI KOUADIO
KONAN NARCISSE
GNAGNE FREDERIC
APKA ESMEL
ESMELY INGRID
KANGA PARFAIT
TOUE APOLLINE
OULAI CYPRIEN
KOUADIO MARIUS
APKA RACHELLE
REAMY BAZIE
KOFFI ALEXIS
DIARRA MOHAMED
KADJA ANOH
KONE FANTAMAN
TOUE APOLLINE
Dr gansere David
Dr mapout bienvenue
Dr Chared Eddicho
Dr kouadosu Francis
dr n'djere
Dr kouassi Landry
dr kouakou amenan Nathalie
dr nikadi dylane
dr akandia aka olive
dembele Hamed
Dr biami Diane
kandam herna
dr Yamara Myriam
Dr Dipoo Philippe
Dr agbo Ana
Konan Emma Konaté
Dr youkam Roctand
Mr kpakpo germain
mr ouadvejo
mme Djikano judith
mr ouadraogo Abdoul
mr ouadraogo Abdoul
mme n'dri Rachelle
mme Konan Emilie
mme gogbo Martine
mr akpoesa azouba
mme aore gràce
mme Touré marie Tano
mme n'takpe Marthe
mme Anthony Tatiana
mme bouatongu habiba
mme kouadio Sandrine
mme Datte Fatouma
mme Ouroho
mme aicha Adeline
mme aboussou Nicole
mme Diomande
pr odjalu
mme n'golo Dr
dr koffi o
dr Diomande zenab
Dr kouadio iol
dr Tano
dr aghaodra
dr Barry
Dr macoto
dr atounmi
cva tihio
dr Ouattara
dr dao a
ya koua
dr kassa
dr yao
Dr gendo Idrich
dr Konan
dr yao
dr ouan
dr moromo
pr alla numba
dr bekooa
dr Coulibaly
dr bom flora
dr matheaat
dr yapi Bénédicte
dr Toua
dr babatunde
dr inahouno
dr abouba
dr rongwa Tancin
dr tresek brascam
dr tresek Tescok Mary
dr Ooouh
dr baaa
mayo
dr Coulibaly
dr casey aime
dr Coulibaly Yaya
dr bamba Aboubacar
de bpami Nina
dr ouahou kasya
dr bana Paul
dr bom kouadio
mme couasty
dr rita
dr meite
dr Hamid lala
dr Diomande Mohamed
dr meite Marina
dr ouattari djakoury
pr Ag Essilier
dr kouadio Roseline
dr kokro Michel
dr mare marian
dr suisa Vianney
dr Edi meelyne
dr niahe Vianney
dr diaba deni
dr diaba louaeco
dr Ettienango
dr oaho Sandrine
dr Touré angelle
dr ouhongo
dr mahio Dominique
dr tchoumou Christophe
dr moitam Nediou
dr kouadio annel
dr moktar isacha
dr n'guessan Ghislaine
dr kiakouou
dr koffi Fabrice
dr datte kouame
dr ouibop
dr gbery doffou
dr Dogbo Eric
dr kouassi Roseline
dr Ouattara ismaela
dr tia alain
dr bamka Richard
dr zanonu tchoko
dr boundwe Chretien
dr fatena yeli mamouna
dr Kouto mory
dr melonga Jonathan
dr Cissé mamourou
dr Kone yaya
Dr Camara
Dr Kouadio
Dr Yéboué
Dr Zégnédé Nadège
Dr Kodjo Valérie
Dr Alloh
Dr Kanga
Dr Kamissoko
Dr Touré
Dr Coulibaly
Dr Soumah
Dr Atsain
Dr Yéboué
Dr Aka
Dr Zégnédé Nadège
IDE Bohiébi
IDE Badiél Abou
IDE Ishmael Kafando
Dr Bogui Herman
Mme Chantal
IDE Eugène
Dr Touré
Dr N'Guessan Michel
Major Asi
Mme Diomandé
IDE Kouonga
IDE Kouassi Kouamé
IDE Bienvenue
IDE Nadia
IDE Ébé
Dr Kamissoko
Dr Agné
Dr Koulibaly
Zongo
Major M'Bra Marcel
IDE Neyaïa
IDE Achi
Mr Odo
Mr Fodjo
Mme Fanta
Mr Daniel
Major M'Bra Marcel
IDE Neyaïa
Dr Bilal
Dr Koné
Dr Kaho Moussa
Dr Marisol
Dr Assa
Mme Yapo
Mme Casuels
Mme Chantal
Dr N'Guessan
Dr Assa Constantïn
Dr Begué Patrice
Mme Soro Kaniija
Mme Beugué
IDE Zogoo Ibot
Mme Sombo Mariette
Mr Ibrahim
Mr Ouedraogo
Mr Bambaago
Mr Modibo
Dr N'Goran Christelle
IDE Eugene
Dr Amétcho Jean
Dr Yao Serge
Dr Touré Djénabou
Dr Bou Ange
Dr Boni
Dr N'Dri
Dr Bitohi
Major
Mme Gba Caritas
Dr Tuo
Dr Adjé Psu Vndi cité
Sage-femme Major Beblo
Dr Kassoum
Dr Synthia
Dr Katamoko
Dr Sakallo
Dr Anyan Jean
Dr Amétchi
Dr Sakaledia
Dr N'Goran
Dr Boni Fabrice
Dr Armand N'Di
Dr Atoby
Dr Tobea Ange
Dr Akpo Adjépo
Major M'Bra Marcel
IDE Neyaïa
IDE Baissolé
Dr Adou Boidy
Mme Dion
Dr Koman Rachel
IDE Baissolé
Mr Kouamé
IDE André
IDE N'Guessan
IDE Atta Angèle
IDE Atsépri
Dr Koné
IDE Kouassi
SF Sonda Mariette
"""

doctors = [line.strip() for line in doctor_list_raw.split("\n") if line.strip()]

# Remove duplicates while preserving order
unique_doctors = []
seen = set()
for d in doctors:
    upper_d = d.upper()
    if upper_d not in seen:
        seen.add(upper_d)
        unique_doctors.append(d)

print("DOCTOR_CANONICAL = {")
for i, d in enumerate(unique_doctors):
    print(f'    "DOC_{i+1:03d}": "{d}",')
print("}")

print("\nDOCTOR_OVERRIDES = {")
for i, d in enumerate(unique_doctors):
    print(f'    "{d.upper()}": "DOC_{i+1:03d}",')
print("}")
