def AXB(A, b, m1=1, n1=1):
    """
    `A`  -- matrix of linear equations
    `b`  -- vector to be solved
    
    Needs:
        BASIC_REDUCTION(0)? in llc
        
    
    """
#     USI answer, m1, n1, rankA, nullA, i, j, k, r, s, flag, p, m, n;
#     MPmatrix_ *matrix_1, *matrix_2, *matrix_3, *matrix_4, *matrix_5, *matrix_6, *matrix_7;
#     MPmatrix_ *Tmp, *Q, *M;
#     char buff[20];
#     FILE *outfile;
#     MPI **XX, **X, *Temp;
#     int e, ss;

    
    matrix_1 = numpy.concatenate((A, b), axis=1).T
    print "The matrix entered in transposed form is:\n\n{}".format(MAT1)
    matrix_3 = numpy.eye(len(MAT1))
    matrix_2 = BASIS_REDUCTION(matrix_1, matrix_3, 0, m1, n1)
    if any(matrix_3.V[:(matrix_3.shape[0] - 1), matrix_3.shape[1] - 1] == 0):
        raise Error("No solution of AX=B")
    print "The interim transformation matrix is\n"
    print matrix_3
    rankA = matrix_2.shape[0]
    nullA = (matrix_1.shape[0]) - (rankA + 1)
    if !nullA:
        print "Unique solution\n"
        matrix_6 = numpy.zeros((1, matrix_1.shape[0] - 1))
        for j in xrange(matrix_1.shape[0] - 1):
            matrix_6.V[0][j] = MINUSI(matrix_3.V[matrix_3.shape[0] - 1][j]);
        print "The solution X of XA^t=B^t is\n"
        return matrix_6
    
    matrix_4 = numpy.zeros((1 + nullA, matrix_1.shape[0] - 1))
    for i in xrange(nullA + 1):
        for j in xrange(matrix_1.shape[0] - 1):
            matrix_4.V[i][j] = COPYI(matrix_3.V[rankA + i][j]);
        
    
    GCDFLAG = 1;
    matrix_5 = BASIS_REDUCTION0(matrix_4, m1, n1);
    MLLLVERBOSE = 0;
    matrix_6 = numpy.zeros((1, matrix_1.shape[0] - 1))
    for j in xrange(matrix_1.shape[0] - 1): 
        (matrix_5.V[matrix_5.shape[0] - 1][j]).S = -((matrix_5.V[matrix_5.shape[0] - 1][j]).S);
                matrix_6.V[0][j] = COPYI(matrix_5.V[matrix_5.shape[0] - 1][j]);
    
    GCDFLAG = 0;
    matrix_7 = DELETE_ROWI(matrix_5.shape[0], matrix_5);
    print "The short basis for nullspace(A^t) is\n"
    PRINTmatrix_(0,matrix_7.shape[0]-1,0,matrix_7.shape[1]-1,matrix_7);
    GetReturn();
    strcpy(buff, "axbbas.out");
    outfile = fopen(buff, "w");
    FPRINTmatrix_(outfile,0,matrix_7.shape[0]-1,0,matrix_7.shape[1]-1,matrix_7);
    fclose(outfile);
    p = nullA;
    m = p + 1;

    print "A short solution X of XA^t=B^t is \n"
    print "b[%u] = ",m); PRINTmatrix_(0,matrix_6.shape[0]-1,0,matrix_6.shape[1]-1,matrix_6);
/*
    strcpy(buff, "axbsol.out");
    outfile = fopen(buff, "w");
    FPRINTmatrix_(outfile,0,matrix_6.shape[0]-1,0,matrix_6.shape[1]-1,matrix_6);
    fclose(outfile);
*/
    print "Do you want to get the shortest multipliers using Fincke_Pohst? (Y/N)\n"
    answer = GetYN();
    XX = (MPI **)mmalloc((USL)(p * sizeof(MPI *)));
    for j in xrange(p):
        XX[j] = ZEROI();
    if answer:
    
        GCDVERBOSE = 1;
        Q = matrix_5;
        n = Q.shape[0];
        while 1:
        
            M = SHORTESTT0(Q, &X);
            for j in xrange(p):
            
                Temp = XX[j];
                XX[j] = ADDI(XX[j], X[j]);
                FREEMPI(Temp);
                FREEMPI(X[j]);
            
            ffree((char *)X, p * sizeof(MPI *));
            if M == NULL:
                break;
            else
            
                for j in xrange(Q.shape[1]):
                
                    FREEMPI(Q.V[n - 1][j]);
                    Q.V[n - 1][j] = COPYI(M.V[0][j]);
                
                FREEmatrix_(matrix_6);
                matrix_6 = M;
            
        
        print "found a shortest solution vector:\n"
    
    else
        Q = matrix_5;
    strcpy(buff, "axb.out");
    outfile = fopen(buff, "w");
    if answer:
        fprintf(outfile, "A shortest solution vector is ");
    else
        fprintf(outfile, "A short multiplier is ");
    if answer:
        print "b[{}]".format(m)
    fprintf(outfile, "b[%u]", m);
    for j in xrange(p):
    
        e = XX[j].S;
        if e == -1:
        
            print "+"
            fprintf(outfile, "+");
            Temp = MINUSI(XX[j]);
            if !EQONEI(Temp):
            
                PRINTI(Temp);
                FPRINTI(outfile, Temp);
            
            print "b[{}]".format(j + 1)
            fprintf(outfile, "b[%u]", j + 1);
            FREEMPI(Temp);
        
        if e == 1:
        
            print "-"
            fprintf(outfile, "-");
            if !EQONEI(XX[j]):
            
                PRINTI(XX[j]);
                FPRINTI(outfile, XX[j]);
            
            print "b[{}]".format(j + 1)
            fprintf(outfile, "b[%u]", j + 1);
        
    
    print "\n"
    fprintf(outfile, "\n=");
    for j in xrange(p):
        FREEMPI(XX[j]);
    ffree((char *)XX, p * sizeof(MPI *));
    for i in xrange(matrix_6.shape[1]):
    
        FPRINTI(outfile, matrix_6.V[0][i]); 
        fprintf(outfile," ");

    
    fprintf(outfile,"\n");
    fclose(outfile);
