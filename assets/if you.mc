setting s1 = {1/2, 1/8, 1/8, 1/8, 1/8};
setting s2 = {0, 1/8, 1/8, 1/8, 1/8};

chord Em = "Em";
Em = Em @ {-1.1, 1.1, 1, 2, 1} % {s1, s2};


chord A = "A";
A = A @ {1, 2.1, 3, 1.1, 3} % {s1, s2};

chord C = "C";
C = C @ {1, 1.1, 2, 3, 2} % {s1, s2};

chord Cm = "Cm";
Cm = Cm @ {1, 2.1, 3, 1.1, 3} % {s1, s2};

chord G = "G";
G = G @ {1, 3.1, 3, 1.1, 3} % {s1, s2};

play((Em * 4 | A * 4 - 12 | C * 2 | Cm * 2 | G * 3 - 12) - 6);


piece c;
c = {{(Em * 4 | A * 4 - 12 | C * 2 | Cm * 2 | G * 3 - 12) - 6}, {25}, 120};
play(c);
score(c);

/*chord Em7 = "Em7";
Em7 = Em7 @ {1, 2, 4, 2} % {1/8, 1/8};
//play(Em7);
chord Cadd9 = "Cadd9";
Cadd9 = Cadd9 @ {1, 2, 4, 3} % {1/8, 1/8};
play(Em7 | Cadd9);*/