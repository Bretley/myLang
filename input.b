/* valid forms of Declaration */
/* Standard Declaration (singlet) */
Int a;

/* Standard Declaration (multiple)*/
Int a b c;

/* Standard Array Declaration */
Int[10] a b c;

/* Multiple Assignment (implied typing)*/
a b c = 1 2 3;

/* Function assignment (one liner) */
f = Int a => a + 1

/* Function assignment (multi-line / block scoped) */
f = Int a b c => {
    1
}
