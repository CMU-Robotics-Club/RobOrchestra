dataFile = fopen('messingAround.txt', 'r');
formatSpec = '%f %f';
sizeA = [3 Inf];

%reads the data into a 3 column array
A = fscanf(dataFile, formatSpec, sizeA);
A = A'; %transpose
fclose(dataFile);

%L = length(A);

%creates two arrays for what should be on the x and y axes
xArr = [];
tArr = [];
for row = 1:L
    x = power(A(row, 1), 2) + power(A(row, 2), 2);
    t = A(row, 3);
    
    xArr = [xArr, x];
    tArr = [tArr, t]
end
 
plot(tArr, xArr)
xlabel('t')
ylabel('x^2 + y^2')