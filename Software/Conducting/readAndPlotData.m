%from https://www.mathworks.com/matlabcentral/answers/22289-read-an-inp
%ut-file-process-it-line-by-line

%at this point, insert the code to initialize the variable you will be
%storing the words in
%then
fid = fopen('./pixyCamera/fileReading_pde/positionData/position20_11_2019_17_01_17.txt','rt');
A = [];
xArr = [];
tArr = [];
fullc = zeros(0, 5);
while true
  thisline = fgetl(fid);
  if ~ischar(thisline); break; end  %end of file
    c = strsplit(thisline, ", ");
    
    disp(c);
    if(numel(c) ~= 5)
        continue;
    end
    for i = 1:5
        if(c{i} == "")
            continue;
        end
        c{i} = str2double(c{i})
        if(isnan(c{i}))
            continue;
        end
    end
    %c is a 5-element cell array
    %Entries are (x, y) position, (x, y) velocity(?), time (ms?)
    %Distance units are pixels?
    
    fullc = [fullc; [c{1}, c{2}, c{3}, c{4}, c{5}]]; %All the data in a civilized format
    A = [A; c];
    v = [c{1}, c{2}];
    meanpos = mean(fullc(:, 1:2));
    %x = norm(v-meanpos); %This seems bad (too many "beats" detected), not sure why
    x = norm(v);
    
    if ~isempty(xArr)
        filterweight = 0.9; %Bigger = more filtering. Keep this between 0 and 1
        x = (1-filterweight)*x + filterweight*xArr(end); %Filter the data
    end
    
    %x = power(c{1}, 2) + power(c{2}, 2);
    t = c{5};
    
    xArr = [xArr, x];
    tArr = [tArr, t];
    plot(tArr, xArr);
end
  disp(A)
  fclose(fid);
%you have now loaded all of the data.