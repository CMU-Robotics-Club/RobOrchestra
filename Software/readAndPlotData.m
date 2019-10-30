%from https://www.mathworks.com/matlabcentral/answers/22289-read-an-inp
%ut-file-process-it-line-by-line

%at this point, insert the code to initialize the variable you will be
%storing the words in
%then
fid = fopen('messingAroundWithoutCommas.txt','rt');
A = [];
xArr = [];
tArr = [];
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
        c{i} = str2double(c{i});
    end 
    A = [A; c];
    x = c{1};
    
    %x = power(c{1}, 2) + power(c{2}, 2);
    t = c{5};
    
    xArr = [xArr, x];
    tArr = [tArr, t];
    plot(tArr, xArr);
end
  disp(A)
  fclose(fid);
%you have now loaded all of the data.