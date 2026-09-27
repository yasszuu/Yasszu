/*
 * Base de données des 100 animaux.
 *
 * Stats de combat (0-100), relatives à la taille de l'animal :
 *   att = puissance offensive (morsure, griffes, cornes…)
 *   def = résistance aux coups (cuir, carapace, masse musculaire…)
 *   agi = agilité / réflexes
 *   end = endurance
 *   int = intelligence / ruse
 * venin  : 0 à 3 (arme toxique ou électrique)
 * armure : 0 à 3 (réduit l'efficacité du venin et des morsures)
 * milieu : aisance sur [terre, eau, air] de 0 à 1
 * extra  : rv (résistance au venin 0-1), tags, bat (tags contre lesquels l'animal est spécialiste), passif (venin défensif)
 */
(function () {
  const list = [];
  function A(nom, g, emoji, sci, wiki, classe, hab, kg, taille, kmh, s, venin, armure, milieu, arme, talent, fait, extra) {
    list.push(Object.assign({
      id: list.length + 1, nom, g, emoji, sci, wiki, classe,
      habitats: hab.split(","), kg, taille, kmh,
      att: s[0], def: s[1], agi: s[2], end: s[3], int: s[4],
      venin, armure, milieu, arme, talent, fait,
      rv: 0, tags: [], bat: [], passif: false
    }, extra || {}));
  }

  // ─────────── Mammifères terrestres ───────────
  A("Lion", "m", "🦁", "Panthera leo", "Lion", "Mammifère", "Savane", 190, 2.5, 80, [85, 60, 65, 55, 70], 0, 0, [1, .3, 0],
    "Crocs de 7 cm, griffes rétractiles", "Rugissement dissuasif", "Seul félin social : le mâle défend son territoire contre tout intrus.", { tags: ["félin"] });
  A("Tigre du Bengale", "m", "🐅", "Panthera tigris tigris", "Bengal tiger", "Mammifère", "Jungle,Forêt", 220, 2.9, 65, [90, 62, 70, 60, 70], 0, 0, [1, .6, 0],
    "Pattes antérieures massives, morsure de 1 000 PSI", "Embuscade silencieuse", "Excellent nageur, il n'hésite pas à chasser dans l'eau.", { tags: ["félin"] });
  A("Tigre de Sibérie", "m", "🐅", "Panthera tigris altaica", "Siberian tiger", "Mammifère", "Forêt,Banquise", 260, 3.2, 60, [90, 65, 65, 65, 70], 0, 0, [1, .55, 0],
    "Coup de patte capable de briser une nuque", "Force colossale", "Le plus grand félin sauvage ; il lui arrive de chasser l'ours brun.", { tags: ["félin"], bat: ["ours"] });
  A("Jaguar", "m", "🐆", "Panthera onca", "Jaguar", "Mammifère", "Jungle,Marais", 100, 2.0, 80, [88, 55, 72, 55, 70], 0, 0, [1, .7, 0],
    "Morsure perforant crânes et carapaces", "Morsure brise-crâne", "Sa morsure est la plus puissante des félins par rapport à sa taille.", { tags: ["félin"], bat: ["caïman"] });
  A("Léopard", "m", "🐆", "Panthera pardus", "Leopard", "Mammifère", "Savane,Forêt", 60, 1.9, 58, [80, 50, 80, 55, 72], 0, 0, [1, .3, 0],
    "Griffes acérées, morsure à la gorge", "Grimpeur hors pair", "Il hisse en haut des arbres des proies plus lourdes que lui.", { tags: ["félin"] });
  A("Guépard", "m", "🐆", "Acinonyx jubatus", "Cheetah", "Mammifère", "Savane", 50, 1.3, 110, [60, 35, 85, 30, 60], 0, 0, [1, .1, 0],
    "Griffes semi-rétractiles, morsure d'étouffement", "Sprint à 110 km/h", "L'animal terrestre le plus rapide, mais il s'épuise en moins d'une minute.", { tags: ["félin"] });
  A("Panthère des neiges", "f", "🐆", "Panthera uncia", "Snow leopard", "Mammifère", "Montagne,Banquise", 45, 1.3, 64, [75, 50, 88, 60, 68], 0, 0, [1, .2, 0],
    "Griffes larges, morsure à la nuque", "Bond de 15 mètres", "Sa longue queue lui sert de balancier sur les falaises.", { tags: ["félin"] });
  A("Puma", "m", "🐆", "Puma concolor", "Cougar", "Mammifère", "Montagne,Forêt", 70, 2.0, 72, [78, 52, 82, 58, 68], 0, 0, [1, .3, 0],
    "Griffes et morsure puissante", "Détente explosive", "Il peut sauter à 5 mètres de haut depuis l'arrêt.", { tags: ["félin"] });
  A("Lynx boréal", "m", "🐈", "Lynx lynx", "Eurasian lynx", "Mammifère", "Forêt,Montagne", 25, 1.1, 70, [70, 45, 78, 55, 65], 0, 0, [1, .3, 0],
    "Griffes, morsure à la gorge", "Ouïe ultra-fine", "Capable de tuer des chevreuils quatre fois plus lourds que lui.", { tags: ["félin"] });
  A("Loup gris", "m", "🐺", "Canis lupus", "Wolf", "Mammifère", "Forêt,Banquise,Prairie", 45, 1.6, 60, [70, 50, 70, 85, 80], 0, 0, [1, .35, 0],
    "Mâchoires de 400 PSI, crocs de 6 cm", "Endurance de marathonien", "Seul, il est vulnérable ; en meute, il abat des bisons.", { tags: ["canidé"] });
  A("Hyène tachetée", "f", "🐾", "Crocuta crocuta", "Spotted hyena", "Mammifère", "Savane", 60, 1.5, 60, [78, 60, 60, 85, 75], 0, 0, [1, .3, 0],
    "Mâchoires broyeuses d'os (1 100 PSI)", "Mâchoires broyeuses", "Elle digère os, sabots et cornes grâce à son estomac ultra-acide.");
  A("Lycaon", "m", "🐕", "Lycaon pictus", "African wild dog", "Mammifère", "Savane", 25, 1.1, 66, [65, 45, 75, 90, 78], 0, 0, [1, .3, 0],
    "Morsures rapides et répétées", "Chasse coordonnée", "Le prédateur au meilleur taux de réussite d'Afrique (80 %).", { tags: ["canidé"] });
  A("Ours brun", "m", "🐻", "Ursus arctos", "Brown bear", "Mammifère", "Forêt,Montagne", 400, 2.5, 56, [88, 80, 45, 75, 70], 0, 1, [1, .5, 0],
    "Griffes de 10 cm, coup de patte dévastateur", "Charge du grizzly", "Un coup de patte de grizzly peut briser la colonne d'un élan.", { tags: ["ours"] });
  A("Ours polaire", "m", "🐻‍❄️", "Ursus maritimus", "Polar bear", "Mammifère", "Banquise,Océan", 500, 2.6, 40, [88, 82, 42, 80, 68], 0, 1, [1, .7, 0],
    "Griffes et crocs de 5 cm", "Nageur arctique", "Le plus grand carnivore terrestre ; il nage des centaines de kilomètres.", { tags: ["ours"], bat: ["phoque"] });
  A("Glouton", "m", "🦡", "Gulo gulo", "Wolverine", "Mammifère", "Banquise,Forêt", 15, 0.9, 48, [80, 70, 60, 80, 60], 0, 1, [1, .3, 0],
    "Mâchoires capables de broyer de la viande gelée", "Rage indomptable", "Il n'hésite pas à chasser un ours de sa carcasse.");
  A("Ratel", "m", "🦡", "Mellivora capensis", "Honey badger", "Mammifère", "Savane,Désert", 10, 0.8, 30, [70, 85, 55, 80, 70], 0, 1, [1, .2, 0],
    "Griffes de fouisseur, peau épaisse et lâche", "Peau indestructible", "Mordu par un cobra, il s'évanouit… puis se réveille et termine son repas.", { rv: 0.8, bat: ["serpent"] });
  A("Éléphant d'Afrique", "m", "🐘", "Loxodonta africana", "African bush elephant", "Mammifère", "Savane", 6000, 3.3, 40, [75, 85, 25, 75, 90], 0, 2, [1, .6, 0],
    "Défenses de 2 m, trompe surpuissante, piétinement", "Charge de 6 tonnes", "Le plus grand animal terrestre ; même les lions évitent les adultes.");
  A("Rhinocéros blanc", "m", "🦏", "Ceratotherium simum", "White rhinoceros", "Mammifère", "Savane", 2300, 4.0, 50, [78, 88, 30, 65, 40], 0, 2, [1, .3, 0],
    "Corne de 1 m, charge à 50 km/h", "Charge cornue", "Sa peau atteint 5 cm d'épaisseur par endroits.");
  A("Hippopotame", "m", "🦛", "Hippopotamus amphibius", "Hippopotamus", "Mammifère", "Rivière,Savane", 1500, 4.0, 30, [85, 82, 30, 60, 50], 0, 2, [.9, 1, 0],
    "Canines de 50 cm, mâchoire ouvrant à 150°", "Territorial furieux", "Il fait plus de victimes humaines que le lion en Afrique.", { bat: ["crocodile"] });
  A("Buffle d'Afrique", "m", "🐃", "Syncerus caffer", "African buffalo", "Mammifère", "Savane", 700, 3.0, 57, [72, 78, 40, 70, 55], 0, 1, [1, .4, 0],
    "Cornes soudées en bouclier frontal", "Casque de corne", "Surnommé « la mort noire », il tue des lions chaque année.");
  A("Bison d'Amérique", "m", "🦬", "Bison bison", "American bison", "Mammifère", "Prairie", 800, 3.2, 56, [70, 80, 40, 80, 45], 0, 1, [1, .3, 0],
    "Cornes, tête massive", "Charge de la prairie", "Malgré sa masse, il franchit d'un bond des obstacles de 1,8 m.");
  A("Girafe", "f", "🦒", "Giraffa camelopardalis", "Giraffe", "Mammifère", "Savane", 1200, 5.5, 60, [60, 60, 35, 60, 45], 0, 1, [1, .05, 0],
    "Ruades à sabots de 30 cm", "Ruade mortelle", "Un seul coup de sabot peut tuer un lion sur le coup.");
  A("Gorille", "m", "🦍", "Gorilla gorilla", "Western gorilla", "Mammifère", "Jungle", 160, 1.7, 40, [80, 70, 50, 55, 85], 0, 0, [1, .05, 0],
    "Bras d'une force colossale, canines de 5 cm", "Force titanesque", "Pacifique de nature, il intimide bien plus qu'il ne combat.", { tags: ["primate"] });
  A("Chimpanzé", "m", "🐒", "Pan troglodytes", "Chimpanzee", "Mammifère", "Jungle,Forêt", 50, 1.2, 40, [70, 45, 75, 55, 95], 0, 0, [1, .05, 0],
    "Force 1,5 fois supérieure à l'humain, morsure", "Stratège primate", "Il utilise des outils et chasse en groupes organisés.", { tags: ["primate"] });
  A("Orang-outan", "m", "🦧", "Pongo pygmaeus", "Bornean orangutan", "Mammifère", "Jungle", 80, 1.4, 30, [65, 55, 55, 50, 92], 0, 0, [1, .05, 0],
    "Envergure de bras de 2,2 m, poigne d'acier", "Poigne d'acier", "Le plus grand animal arboricole du monde.", { tags: ["primate"] });
  A("Babouin chacma", "m", "🐒", "Papio ursinus", "Chacma baboon", "Mammifère", "Savane,Montagne", 30, 1.0, 45, [65, 45, 70, 60, 80], 0, 0, [1, .1, 0],
    "Canines plus longues que celles du lion", "Canines de fauve", "Ses canines rivalisent en taille avec celles d'un léopard.", { tags: ["primate"] });
  A("Sanglier", "m", "🐗", "Sus scrofa", "Wild boar", "Mammifère", "Forêt", 100, 1.6, 48, [70, 70, 50, 75, 60], 0, 1, [1, .4, 0],
    "Défenses tranchantes comme des rasoirs", "Charge du solitaire", "Un vieux mâle solitaire peut éventrer un chien de chasse.", { rv: 0.3 });
  A("Élan", "m", "🫎", "Alces alces", "Moose", "Mammifère", "Forêt,Banquise", 500, 3.0, 56, [65, 70, 40, 75, 45], 0, 1, [1, .6, 0],
    "Bois de 1,8 m, sabots tranchants", "Coup de sabot", "Excellent nageur, il plonge jusqu'à 6 m pour brouter.");
  A("Cerf élaphe", "m", "🦌", "Cervus elaphus", "Red deer", "Mammifère", "Forêt", 200, 2.2, 70, [55, 50, 60, 65, 50], 0, 0, [1, .3, 0],
    "Bois ramifiés", "Brame du dominant", "Ses bois repoussent chaque année, jusqu'à 2,5 cm par jour.");
  A("Zèbre des plaines", "m", "🦓", "Equus quagga", "Plains zebra", "Mammifère", "Savane", 350, 2.4, 65, [50, 50, 60, 70, 50], 0, 0, [1, .3, 0],
    "Ruades et morsures", "Ruade fracassante", "Sa ruade peut briser la mâchoire d'un lion.");
  A("Gnou bleu", "m", "🐃", "Connochaetes taurinus", "Blue wildebeest", "Mammifère", "Savane", 250, 2.3, 80, [45, 50, 55, 85, 40], 0, 0, [1, .3, 0],
    "Cornes recourbées", "Migration infinie", "1,5 million de gnous migrent chaque année dans le Serengeti.");
  A("Kangourou roux", "m", "🦘", "Osphranter rufus", "Red kangaroo", "Mammifère", "Désert,Prairie", 85, 1.6, 70, [65, 50, 70, 70, 50], 0, 0, [1, .4, 0],
    "Coups de pieds griffus", "Double coup de pied", "Il lui arrive de noyer ses poursuivants en les attirant dans l'eau.");
  A("Diable de Tasmanie", "m", "😈", "Sarcophilus harrisii", "Tasmanian devil", "Mammifère", "Forêt", 8, 0.65, 25, [72, 55, 50, 60, 50], 0, 0, [1, .3, 0],
    "Mâchoires broyeuses d'os", "Morsure infernale", "La morsure la plus puissante des mammifères par rapport à sa taille.");
  A("Renard roux", "m", "🦊", "Vulpes vulpes", "Red fox", "Mammifère", "Forêt,Prairie", 7, 0.9, 50, [50, 35, 80, 60, 85], 0, 0, [1, .3, 0],
    "Crocs fins", "Ruse légendaire", "Il utilise le champ magnétique terrestre pour bondir sur ses proies.", { tags: ["canidé"] });
  A("Coyote", "m", "🐺", "Canis latrans", "Coyote", "Mammifère", "Prairie,Désert", 14, 1.1, 65, [55, 40, 75, 75, 80], 0, 0, [1, .3, 0],
    "Crocs, morsures rapides", "Opportuniste", "Il a colonisé toute l'Amérique du Nord, jusqu'au cœur des villes.", { tags: ["canidé"] });
  A("Suricate", "m", "🐾", "Suricata suricatta", "Meerkat", "Mammifère", "Désert", 0.8, 0.3, 32, [40, 35, 80, 60, 75], 0, 0, [1, .05, 0],
    "Griffes de fouisseur", "Sentinelle vigilante", "Partiellement résistant au venin de scorpion, qu'il dévore.", { rv: 0.5, bat: ["scorpion"] });
  A("Porc-épic à crête", "m", "🦔", "Hystrix cristata", "Crested porcupine", "Mammifère", "Savane,Forêt", 20, 0.9, 16, [40, 92, 30, 55, 45], 0, 2, [1, .2, 0],
    "Piquants de 35 cm détachables", "Hérisse-piquants", "Des lions sont morts de blessures infectées par ses piquants.");
  A("Tatou à neuf bandes", "m", "🐾", "Dasypus novemcinctus", "Nine-banded armadillo", "Mammifère", "Prairie,Forêt", 5, 0.8, 48, [15, 85, 40, 50, 35], 0, 3, [1, .4, 0],
    "Carapace osseuse, griffes", "Carapace osseuse", "Il retient sa respiration 6 minutes et marche au fond de l'eau.");
  A("Pangolin terrestre", "m", "🐾", "Smutsia temminckii", "Ground pangolin", "Mammifère", "Savane", 10, 1.0, 5, [15, 92, 20, 50, 40], 0, 3, [1, .1, 0],
    "Écailles de kératine tranchantes", "Boule blindée", "Roulé en boule, même un lion ne parvient pas à le percer.");
  A("Dromadaire", "m", "🐪", "Camelus dromedarius", "Dromedary", "Mammifère", "Désert", 500, 3.0, 65, [45, 60, 35, 95, 45], 0, 1, [1, .1, 0],
    "Morsures, coups de pattes", "Endurance du désert", "Il survit deux semaines sans boire sous 50 °C.");
  A("Mangouste grise", "f", "🐾", "Urva edwardsii", "Indian grey mongoose", "Mammifère", "Prairie,Forêt", 1.5, 0.45, 32, [60, 40, 95, 60, 70], 0, 0, [1, .1, 0],
    "Morsure à la tête, réflexes éclair", "Réflexes anti-cobra", "Ses récepteurs nerveux sont insensibles au venin de cobra.", { rv: 0.9, bat: ["serpent"] });

  // ─────────── Mammifères marins ───────────
  A("Orque", "f", "🐋", "Orcinus orca", "Orca", "Mammifère", "Océan,Banquise", 5000, 7, 56, [92, 75, 70, 85, 95], 0, 1, [.02, 1, 0],
    "Dents de 10 cm, coups de rostre", "Tactique de meute", "Elle chasse le grand requin blanc pour ne manger que son foie.", { bat: ["requin", "phoque", "manchot"] });
  A("Cachalot", "m", "🐋", "Physeter macrocephalus", "Sperm whale", "Mammifère", "Océan", 40000, 16, 35, [75, 90, 30, 95, 80], 0, 2, [0, 1, 0],
    "Mâchoire dentée de 5 m, tête-bélier", "Plongée abyssale", "Il plonge à 2 000 m pour affronter les calmars géants.", { bat: ["calmar"] });
  A("Baleine bleue", "f", "🐋", "Balaenoptera musculus", "Blue whale", "Mammifère", "Océan", 150000, 28, 50, [20, 85, 20, 95, 60], 0, 2, [0, 1, 0],
    "Coups de queue titanesques", "Masse colossale", "Le plus grand animal ayant jamais existé ; elle n'a pas de dents.");
  A("Grand dauphin", "m", "🐬", "Tursiops truncatus", "Common bottlenose dolphin", "Mammifère", "Océan", 300, 3.0, 35, [60, 55, 90, 80, 95], 0, 0, [0, 1, 0],
    "Coups de rostre dans les flancs", "Écholocation", "Des groupes de dauphins tuent des requins à coups de rostre.", { bat: ["requin"] });
  A("Morse", "m", "🦭", "Odobenus rosmarus", "Walrus", "Mammifère", "Banquise,Océan", 1200, 3.3, 35, [65, 85, 25, 70, 50], 0, 2, [.4, 1, 0],
    "Défenses d'ivoire de 1 m", "Défenses d'ivoire", "Ses défenses peuvent blesser gravement un ours polaire.", { tags: ["phoque"] });
  A("Éléphant de mer du Sud", "m", "🦭", "Mirounga leonina", "Southern elephant seal", "Mammifère", "Océan,Banquise", 3000, 5.5, 25, [60, 80, 25, 80, 45], 0, 2, [.3, 1, 0],
    "Canines, poids écrasant", "Colosse des glaces", "Les mâles se livrent des combats sanglants de 4 tonnes.", { tags: ["phoque"] });
  A("Léopard de mer", "m", "🦭", "Hydrurga leptonyx", "Leopard seal", "Mammifère", "Banquise,Océan", 400, 3.2, 40, [80, 60, 70, 70, 70], 0, 1, [.3, 1, 0],
    "Mâchoire reptilienne, canines de 2,5 cm", "Chasseur des glaces", "Le seul phoque qui chasse d'autres phoques.", { tags: ["phoque"], bat: ["manchot"] });
  A("Loutre de mer", "f", "🦦", "Enhydra lutris", "Sea otter", "Mammifère", "Océan", 30, 1.3, 9, [40, 45, 75, 65, 85], 0, 0, [.3, 1, 0],
    "Dents broyeuses de coquillages", "Utilisatrice d'outils", "Elle casse les oursins avec une pierre posée sur son ventre.", { bat: ["crabe"] });

  // ─────────── Oiseaux ───────────
  A("Aigle royal", "m", "🦅", "Aquila chrysaetos", "Golden eagle", "Oiseau", "Montagne", 5, 2.2, 240, [80, 35, 85, 60, 70], 0, 0, [.6, 0, 1],
    "Serres de 5 cm, pression de 200 kg", "Piqué à 240 km/h", "Il capture parfois des chèvres et de jeunes cerfs.", { tags: ["rapace"] });
  A("Harpie féroce", "f", "🦅", "Harpia harpyja", "Harpy eagle", "Oiseau", "Jungle", 8, 2.0, 80, [88, 40, 80, 55, 70], 0, 0, [.6, 0, 1],
    "Serres de 12 cm, aussi grandes que celles d'un grizzly", "Serres de grizzly", "Elle arrache paresseux et singes des branches.", { tags: ["rapace"], bat: ["primate"] });
  A("Pygargue à tête blanche", "m", "🦅", "Haliaeetus leucocephalus", "Bald eagle", "Oiseau", "Rivière,Forêt", 5, 2.2, 160, [72, 35, 80, 60, 65], 0, 0, [.6, .1, 1],
    "Serres puissantes, bec crochu", "Pêcheur aérien", "Emblème des États-Unis, il vole volontiers les proies des autres.", { tags: ["rapace"] });
  A("Faucon pèlerin", "m", "🦅", "Falco peregrinus", "Peregrine falcon", "Oiseau", "Montagne", 1, 1.1, 390, [70, 25, 95, 55, 70], 0, 0, [.4, 0, 1],
    "Serres et bec à « dent » tranchante", "Piqué à 390 km/h", "L'animal le plus rapide du monde, en piqué.", { tags: ["rapace"] });
  A("Grand-duc d'Europe", "m", "🦉", "Bubo bubo", "Eurasian eagle-owl", "Oiseau", "Forêt,Montagne", 3, 1.8, 80, [75, 35, 80, 55, 65], 0, 0, [.5, 0, 1],
    "Serres, attaque silencieuse", "Vol silencieux", "Il chasse des renards et même d'autres rapaces.", { tags: ["rapace"] });
  A("Autruche", "f", "🐦", "Struthio camelus", "Common ostrich", "Oiseau", "Savane", 120, 2.7, 70, [65, 50, 60, 80, 30], 0, 0, [1, .1, 0],
    "Coup de pied avec griffe de 10 cm", "Coup de pied éventreur", "Son coup de pied peut tuer un lion.");
  A("Casoar à casque", "m", "🐦", "Casuarius casuarius", "Southern cassowary", "Oiseau", "Jungle", 60, 1.8, 50, [75, 55, 65, 65, 35], 0, 1, [1, .4, 0],
    "Griffe-poignard de 12 cm", "Griffe-poignard", "Souvent considéré comme l'oiseau le plus dangereux du monde.");
  A("Condor des Andes", "m", "🦅", "Vultur gryphus", "Andean condor", "Oiseau", "Montagne", 12, 3.2, 90, [35, 35, 50, 80, 55], 0, 0, [.6, 0, 1],
    "Bec crochu", "Maître des thermiques", "Il peut planer 170 km sans battre des ailes.");
  A("Manchot empereur", "m", "🐧", "Aptenodytes forsteri", "Emperor penguin", "Oiseau", "Banquise", 30, 1.2, 9, [30, 50, 50, 90, 45], 0, 0, [.4, .9, 0],
    "Bec, battements d'ailerons", "Plongeur des glaces", "Il plonge à plus de 500 m de profondeur.", { tags: ["manchot"] });
  A("Albatros hurleur", "m", "🐦", "Diomedea exulans", "Wandering albatross", "Oiseau", "Océan", 10, 3.5, 110, [35, 30, 55, 95, 50], 0, 0, [.3, .5, 1],
    "Bec crochu tranchant", "Envergure record", "La plus grande envergure du monde vivant : 3,5 m.");
  A("Serpentaire", "m", "🐦", "Sagittarius serpentarius", "Secretarybird", "Oiseau", "Savane", 4, 1.3, 60, [70, 40, 80, 60, 60], 0, 0, [1, 0, .7],
    "Coups de pied foudroyants (15 millisecondes)", "Tueur de serpents", "Il tue les serpents venimeux à coups de pied d'une précision chirurgicale.", { rv: 0.4, bat: ["serpent"] });

  // ─────────── Reptiles ───────────
  A("Crocodile marin", "m", "🐊", "Crocodylus porosus", "Saltwater crocodile", "Reptile", "Marais,Océan", 700, 5.5, 29, [95, 85, 40, 55, 50], 0, 3, [.55, 1, 0],
    "Morsure de 3 700 PSI, la plus puissante mesurée", "Rouleau de la mort", "La morsure la plus puissante jamais mesurée chez un animal vivant.", { tags: ["crocodile"] });
  A("Crocodile du Nil", "m", "🐊", "Crocodylus niloticus", "Nile crocodile", "Reptile", "Rivière,Savane", 400, 4.5, 30, [92, 82, 40, 55, 50], 0, 3, [.55, 1, 0],
    "Morsure de 3 000 PSI, 66 dents coniques", "Embuscade aquatique", "Il attaque zèbres et gnous lors de la traversée des rivières.", { tags: ["crocodile"] });
  A("Alligator d'Amérique", "m", "🐊", "Alligator mississippiensis", "American alligator", "Reptile", "Marais", 350, 4.0, 32, [88, 80, 40, 55, 50], 0, 3, [.55, 1, 0],
    "Morsure de 2 980 PSI", "Rouleau de la mort", "Il existe presque inchangé depuis 37 millions d'années.", { tags: ["crocodile", "caïman"] });
  A("Dragon de Komodo", "m", "🦎", "Varanus komodoensis", "Komodo dragon", "Reptile", "Savane,Forêt", 80, 2.8, 20, [75, 65, 40, 55, 50], 1, 2, [1, .5, 0],
    "Dents dentelées, glandes à venin anticoagulant", "Morsure venimeuse", "Il traque des buffles blessés pendant des jours.");
  A("Anaconda vert", "m", "🐍", "Eunectes murinus", "Green anaconda", "Reptile", "Marais,Rivière", 70, 5.5, 16, [85, 60, 35, 60, 40], 0, 1, [.4, 1, 0],
    "Constriction mortelle", "Étreinte fatale", "Le serpent le plus lourd du monde : il avale des caïmans.", { tags: ["serpent"], bat: ["caïman"] });
  A("Python réticulé", "m", "🐍", "Malayopython reticulatus", "Reticulated python", "Reptile", "Jungle", 75, 6.5, 10, [85, 55, 40, 60, 40], 0, 1, [.8, .7, 0],
    "Constriction, plus de 100 dents recourbées", "Étreinte fatale", "Le plus long serpent du monde, jusqu'à 7 m.", { tags: ["serpent"] });
  A("Cobra royal", "m", "🐍", "Ophiophagus hannah", "King cobra", "Reptile", "Jungle", 6, 4.0, 19, [70, 35, 70, 50, 55], 3, 0, [1, .4, 0],
    "Crochets injectant 7 ml de neurotoxine", "Venin d'éléphant", "Une seule morsure peut tuer un éléphant en quelques heures.", { tags: ["serpent"], bat: ["serpent"] });
  A("Mamba noir", "m", "🐍", "Dendroaspis polylepis", "Black mamba", "Reptile", "Savane", 1.6, 2.5, 20, [72, 30, 85, 50, 55], 3, 0, [1, .1, 0],
    "Frappes multiples, neurotoxines foudroyantes", "Frappe éclair", "Le serpent le plus rapide d'Afrique ; sa morsure tue en 20 minutes.", { tags: ["serpent"] });
  A("Taïpan du désert", "m", "🐍", "Oxyuranus microlepidotus", "Inland taipan", "Reptile", "Désert", 1.8, 2.0, 15, [65, 30, 75, 45, 50], 3, 0, [1, .1, 0],
    "Venin le plus toxique de tous les serpents", "Venin suprême", "Une seule morsure contient de quoi tuer 100 humains.", { tags: ["serpent"] });
  A("Crotale diamantin", "m", "🐍", "Crotalus adamanteus", "Eastern diamondback rattlesnake", "Reptile", "Prairie,Marais", 2.5, 1.8, 5, [62, 35, 55, 45, 45], 2, 0, [1, .3, 0],
    "Crochets hémotoxiques", "Détection thermique", "Ses fossettes détectent la chaleur de ses proies dans le noir total.", { tags: ["serpent"] });
  A("Tortue alligator", "f", "🐢", "Macrochelys temminckii", "Alligator snapping turtle", "Reptile", "Rivière,Marais", 80, 0.8, 5, [70, 95, 15, 60, 30], 0, 3, [.3, 1, 0],
    "Bec crochu capable de sectionner un doigt", "Langue-leurre", "Elle attire les poissons avec un leurre en forme de ver sur sa langue.");
  A("Tortue géante des Galápagos", "f", "🐢", "Chelonoidis niger", "Galápagos tortoise", "Reptile", "Prairie", 250, 1.5, 0.3, [15, 98, 5, 90, 30], 0, 3, [1, .1, 0],
    "Carapace blindée, bec corné", "Forteresse vivante", "Elle peut vivre plus de 150 ans.");
  A("Monstre de Gila", "m", "🦎", "Heloderma suspectum", "Gila monster", "Reptile", "Désert", 1.5, 0.5, 2, [45, 60, 20, 50, 35], 2, 1, [1, .1, 0],
    "Morsure venimeuse « mâchée »", "Mâchoire-étau", "Il mâche son venin dans la plaie au lieu de l'injecter.");
  A("Gavial du Gange", "m", "🐊", "Gavialis gangeticus", "Gharial", "Reptile", "Rivière", 250, 5.0, 25, [65, 80, 40, 55, 40], 0, 3, [.3, 1, 0],
    "Museau fin armé de 110 dents", "Pêcheur éclair", "Son museau en baguette est taillé pour attraper les poissons.", { tags: ["crocodile"] });

  // ─────────── Poissons ───────────
  A("Grand requin blanc", "m", "🦈", "Carcharodon carcharias", "Great white shark", "Poisson", "Océan", 1100, 5.5, 56, [92, 70, 60, 70, 55], 0, 1, [0, 1, 0],
    "300 dents dentelées en rangées", "Attaque verticale", "Il perçoit une goutte de sang diluée dans 100 litres d'eau.", { tags: ["requin"], bat: ["phoque"] });
  A("Requin tigre", "m", "🦈", "Galeocerdo cuvier", "Tiger shark", "Poisson", "Océan", 600, 4.5, 32, [88, 65, 55, 70, 50], 0, 1, [0, 1, 0],
    "Dents découpeuses de carapaces", "Mange-tout", "On a retrouvé des plaques d'immatriculation dans son estomac.", { tags: ["requin"] });
  A("Requin-bouledogue", "m", "🦈", "Carcharhinus leucas", "Bull shark", "Poisson", "Océan,Rivière", 200, 3.4, 40, [85, 60, 60, 70, 50], 0, 1, [0, 1, 0],
    "Morsure de 6 000 N, la plus forte des requins à taille égale", "Eau douce et salée", "Il remonte l'Amazone et le Mississippi sur des milliers de km.", { tags: ["requin"] });
  A("Grand requin-marteau", "m", "🦈", "Sphyrna mokarran", "Great hammerhead", "Poisson", "Océan", 450, 6.0, 40, [80, 60, 70, 65, 55], 0, 1, [0, 1, 0],
    "Dents dentelées, tête-marteau", "Radar électrique", "Il détecte les champs électriques des raies enfouies dans le sable.", { tags: ["requin"], rv: 0.5 });
  A("Requin-baleine", "m", "🦈", "Rhincodon typus", "Whale shark", "Poisson", "Océan", 19000, 12, 5, [10, 85, 20, 85, 30], 0, 2, [0, 1, 0],
    "Aucune : filtreur pacifique", "Peau de 10 cm", "Le plus grand poisson du monde, totalement inoffensif.", { tags: ["requin"] });
  A("Espadon", "m", "🗡️", "Xiphias gladius", "Swordfish", "Poisson", "Océan", 400, 4.0, 97, [80, 55, 75, 70, 45], 0, 0, [0, 1, 0],
    "Rostre-épée de 1,2 m", "Épée tranchante", "Des espadons ont déjà transpercé des coques de bateaux.");
  A("Voilier de l'Indo-Pacifique", "m", "🐟", "Istiophorus platypterus", "Indo-Pacific sailfish", "Poisson", "Océan", 90, 3.0, 110, [65, 45, 85, 65, 45], 0, 0, [0, 1, 0],
    "Rostre fouetteur", "Nageur supersonique", "Il change de couleur en chassant pour désorienter ses proies.");
  A("Piranha à ventre rouge", "m", "🐟", "Pygocentrus nattereri", "Red-bellied piranha", "Poisson", "Rivière", 1, 0.33, 25, [75, 40, 60, 50, 40], 0, 0, [0, 1, 0],
    "Dents triangulaires tranchantes comme des rasoirs", "Frénésie", "À taille égale, sa morsure surpasse celle du T. rex.");
  A("Grand barracuda", "m", "🐟", "Sphyraena barracuda", "Great barracuda", "Poisson", "Océan", 20, 1.6, 58, [75, 40, 70, 55, 45], 0, 0, [0, 1, 0],
    "Crocs en forme de poignards", "Torpille dentée", "Il accélère à 58 km/h en une fraction de seconde.");
  A("Poisson-pierre", "m", "🪨", "Synanceia verrucosa", "Reef stonefish", "Poisson", "Océan", 2, 0.4, 3, [30, 70, 20, 50, 30], 3, 1, [0, 1, 0],
    "13 épines dorsales ultra-venimeuses", "Camouflage parfait", "Le poisson le plus venimeux du monde.", { passif: true });
  A("Murène géante", "f", "🐍", "Gymnothorax javanicus", "Giant moray", "Poisson", "Océan", 30, 3.0, 20, [75, 50, 55, 55, 40], 0, 0, [0, 1, 0],
    "Double mâchoire pharyngienne", "Mâchoire-alien", "Une seconde mâchoire jaillit de sa gorge pour agripper la proie.");
  A("Anguille électrique", "f", "⚡", "Electrophorus electricus", "Electric eel", "Poisson", "Rivière", 20, 2.5, 10, [70, 40, 30, 55, 40], 2, 0, [.1, 1, 0],
    "Décharges de 860 volts", "Décharge de 860 V", "Elle peut bondir hors de l'eau pour électrocuter un prédateur.", { electrique: true });
  A("Silure glane", "m", "🐟", "Silurus glanis", "Wels catfish", "Poisson", "Rivière", 100, 2.7, 15, [60, 55, 35, 65, 40], 0, 0, [.05, 1, 0],
    "Bouche béante à mille petites dents", "Aspiration géante", "En France, il gobe des pigeons au bord de l'eau.");

  // ─────────── Amphibiens ───────────
  A("Salamandre géante de Chine", "f", "🦎", "Andrias davidianus", "Chinese giant salamander", "Amphibien", "Rivière,Montagne", 50, 1.8, 5, [45, 50, 20, 60, 30], 0, 0, [.3, 1, 0],
    "Morsure rapide par aspiration", "Géante amphibie", "Le plus grand amphibien du monde, jusqu'à 1,8 m.");
  A("Phyllobate terrible", "m", "🐸", "Phyllobates terribilis", "Golden poison frog", "Amphibien", "Jungle", 0.03, 0.05, 3, [5, 20, 40, 40, 20], 3, 0, [1, .6, 0],
    "Peau imprégnée de batrachotoxine", "Peau mortelle", "Sa peau contient assez de toxine pour tuer 10 humains.", { passif: true });

  // ─────────── Invertébrés ───────────
  A("Pieuvre géante du Pacifique", "f", "🐙", "Enteroctopus dofleini", "Giant Pacific octopus", "Invertébré", "Océan", 50, 6.0, 40, [70, 45, 85, 45, 95], 1, 0, [.1, 1, 0],
    "2 240 ventouses, bec venimeux", "Maître du camouflage", "Elle a déjà été filmée en train de noyer un requin.", { tags: ["calmar"], bat: ["crabe"] });
  A("Calmar géant", "m", "🦑", "Architeuthis dux", "Giant squid", "Invertébré", "Océan", 275, 12, 30, [75, 40, 60, 55, 70], 0, 0, [0, 1, 0],
    "Ventouses dentées, bec tranchant", "Yeux géants", "Ses yeux de 27 cm sont les plus grands du règne animal.", { tags: ["calmar"] });
  A("Cuboméduse", "f", "🪼", "Chironex fleckeri", "Chironex fleckeri", "Invertébré", "Océan", 2, 3.0, 7, [40, 15, 40, 50, 5], 3, 0, [0, 1, 0],
    "60 tentacules de 3 m couverts de cellules urticantes", "Venin cardiotoxique", "Son venin peut arrêter un cœur humain en 3 minutes.");
  A("Crevette-mante paon", "f", "🦐", "Odontodactylus scyllarus", "Peacock mantis shrimp", "Invertébré", "Océan", 0.1, 0.18, 80, [95, 60, 90, 50, 40], 0, 1, [0, 1, 0],
    "Poings frappant à 80 km/h avec cavitation", "Coup de poing supersonique", "Son coup crée une bulle de cavitation à plusieurs milliers de degrés.", { bat: ["crabe"] });
  A("Scorpion Deathstalker", "m", "🦂", "Leiurus quinquestriatus", "Deathstalker", "Invertébré", "Désert", 0.003, 0.1, 2, [50, 55, 50, 70, 20], 2, 1, [1, 0, 0],
    "Dard neurotoxique, pinces", "Dard mortel", "Son venin est étudié pour traiter certains cancers du cerveau.", { tags: ["scorpion"] });
  A("Veuve noire", "f", "🕷️", "Latrodectus mactans", "Latrodectus mactans", "Invertébré", "Prairie,Forêt", 0.001, 0.013, 1, [35, 20, 40, 40, 25], 2, 0, [1, 0, 0],
    "Crochets à latrotoxine", "Toile d'acier", "À poids égal, sa soie est plus résistante que l'acier.");
  A("Frelon géant d'Asie", "m", "🐝", "Vespa mandarinia", "Vespa mandarinia", "Invertébré", "Forêt", 0.006, 0.05, 40, [70, 40, 75, 70, 40], 2, 1, [.8, 0, 1],
    "Dard de 6 mm, venin nécrosant", "Commando volant", "30 frelons peuvent massacrer 30 000 abeilles en 3 heures.");
  A("Fourmi balle de fusil", "f", "🐜", "Paraponera clavata", "Paraponera clavata", "Invertébré", "Jungle", 0.0002, 0.03, 1, [60, 45, 50, 60, 30], 2, 1, [1, 0, 0],
    "Aiguillon à poneratoxine", "Douleur absolue", "Sa piqûre est la plus douloureuse au monde : 24 h de souffrance.");
  A("Mygale Goliath", "f", "🕷️", "Theraphosa blondi", "Goliath birdeater", "Invertébré", "Jungle", 0.175, 0.3, 1, [55, 45, 40, 50, 25], 1, 1, [1, 0, 0],
    "Crochets de 2,5 cm, poils urticants", "Poils urticants", "La plus grosse araignée du monde, de la taille d'une assiette.");
  A("Scolopendre géante", "f", "🐛", "Scolopendra gigantea", "Scolopendra gigantea", "Invertébré", "Jungle", 0.05, 0.3, 2, [70, 55, 65, 60, 25], 2, 1, [1, .1, 0],
    "Forcipules venimeux", "Chasseuse de chauves-souris", "Suspendue aux plafonds des grottes, elle attrape des chauves-souris en vol.");
  A("Crabe de cocotier", "m", "🦀", "Birgus latro", "Coconut crab", "Invertébré", "Jungle,Océan", 4, 1.0, 1, [70, 85, 20, 70, 45], 0, 3, [1, .2, 0],
    "Pinces de 3 300 newtons", "Pince brise-noix", "Sa pince est la plus puissante de tous les crustacés.", { tags: ["crabe"] });

  window.ANIMALS = list;

  window.HABITATS = {
    "Savane":   { color: "#fd7d24", text: "#fff" },
    "Jungle":   { color: "#4ea34e", text: "#fff" },
    "Forêt":    { color: "#729f3f", text: "#fff" },
    "Prairie":  { color: "#9bcc50", text: "#212121" },
    "Océan":    { color: "#4592c4", text: "#fff" },
    "Rivière":  { color: "#53a4cf", text: "#fff" },
    "Marais":   { color: "#7b62a3", text: "#fff" },
    "Banquise": { color: "#51c4e7", text: "#212121" },
    "Montagne": { color: "#a38c21", text: "#fff" },
    "Désert":   { color: "#f7de3f", text: "#212121" }
  };

  window.CLASSES = ["Mammifère", "Oiseau", "Reptile", "Poisson", "Amphibien", "Invertébré"];
})();
