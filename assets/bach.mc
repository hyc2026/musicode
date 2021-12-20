setting s = {1, 2, 3, 1.1, 2.1, 3, 1.1, 2.1};

chord C = "C";
//C = C @ s % {1/8, 1/8} * 2;

chord C7sus4 = "C7sus4";
//C7sus4 = C7sus4 @ s % {1/8, 1/8} * 2;

chord G7 = "G7";
G7 = G7 / 2;
//G7 = G7 @ s % {1/8, 1/8} * 2;


chord res = C | C7sus4 | G7 - 12 | C;
play(res);

piece c;
c = {{res}};
score(c);