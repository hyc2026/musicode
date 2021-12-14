setting s1 = {1/8, 1/8, 1/8, 1/8, 1/8+1/16, 3/16, 1/16, 1/16};
s1 = {s1, s1, 80};
chord bar1_melody1 = {"E4", "G4", "C5", "D5", "D5", "E5", "G4", "G4"};
bar1_melody1 = bar1_melody1 % s1;
chord bar1_melody2 = {"E3", "G3", "G3", "G3", "G3", "C4", "E3", "E3"};
bar1_melody2 = bar1_melody2 % s1;

setting s2 = {1/8, 1/8, 1/8, 1/16, 1/16, 1/8+1/16, 5/16};
s2 = {s2, s2, 80};
chord bar2_melody1 = {"A4", "A4", "A4", "C5", "C5", "D5", "D5"};
bar2_melody1 = bar2_melody1 % s2;
chord bar2_melody2 = {"F3", "F3", "F3", "F3", "A3", "B3", "B3"};
bar2_melody2 = bar2_melody2 % s2;

setting s3 = {1/4, 1/8, 1/16, 1/16, 1/8, 1/8+1/16, 1/16, 1/16, 1/16};
s3 = {s3, s3, 80};
chord bar3_melody1 = {"C5", "C5", "A4", "G4", "E4", "G4", "E4", "E4", "G4"};
bar3_melody1 = bar3_melody1 % s3;
chord bar3_melody2 = {"A3", "A3", "E3", "E3", "C3", "E3", "C3", "C3", "E3"};
bar3_melody2 = bar3_melody2 % s3;

setting s4 = {1/4, 1/8+1/16, 1/16, 1/8, 3/8};
s4 = {s4, s4, 80};
chord bar4_melody1 = {"A4", "G4", "E4", "G4", "D4"};
bar4_melody1 = bar4_melody1 % s4;
chord bar4_melody2 = {"F3", "E3", "C3", "D3", "B2"};
bar4_melody2 = bar4_melody2 % s4;


chord melody1 = bar1_melody1 | bar2_melody1 | bar3_melody1 | bar4_melody1;
chord melody2 = bar1_melody2 | bar2_melody2 | bar3_melody2 | bar4_melody2;

chord Cmaj = "Cmaj";
Cmaj = Cmaj @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8};
chord Fmaj = "Fmaj";
Fmaj = Fmaj @ {1, 2, 3, 1.1} % {1/8, 1/8};
chord Gmaj1 = "Gmaj";
Gmaj1 = Gmaj1 @ {1, 2, 3, 1.1} % {1/8, 1/8};
chord Amin = "Amin";
Amin = Amin @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8};
chord Gmaj2 = "Gmaj";
Gmaj2 = Gmaj2 @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8};
chord accompany = Cmaj - 12 | Fmaj - 24 | Gmaj1 - 24 | Amin - 24 | Gmaj2 - 12;

piece c;
c = {{melody1, melody2, accompany}, {74, 69, 1}, 60};
play(c);
score(c);

/*chord melody = {"G4", "A4", "C5", "D5", "D5"};
melody = melody % {{1/4+1/8, 1/16, 1/16, 1/8, 7/8}, {1/4+1/8, 1/16, 1/16, 1/8, 7/8}};
play(melody);*/

/*note a = {"A", 5, 1};
chord b ;
b = {"C5", "E5", "G5", "B5", "C6"};
b = b % {1, 1/8};

chord Cmaj = "Cmaj";
Cmaj = Cmaj @ {1, 2, 3, -1.1} % {1/8, 1/8} * 2 ;
play(Cmaj);*/

/*
chord Dmaj7 = "Dmaj7";
Dmaj7 = Dmaj7 @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8} * 2;
chord Amaj7 = "Amaj7";
Amaj7 = Amaj7 @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8} * 2;
chord Bmaj7 = "Bmaj7";
Bmaj7 = Bmaj7 @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8} * 2;
chord Gmaj7 = "Gmaj7";
Gmaj7 = Gmaj7 @ {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1} % {1/8, 1/8} * 2;

chord res = Dmaj7 | Amaj7 - 12 | Bmaj7 - 12 | Gmaj7;
play(res);*/