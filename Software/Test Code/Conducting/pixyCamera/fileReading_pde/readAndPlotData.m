%from https://www.mathworks.com/matlabcentral/answers/22289-read-an-inp
%ut-file-process-it-line-by-line

%at this point, insert the code to initialize the variable you will be
%storing the words in
%then
fid = fopen('positionData\position20_11_2019_17_02_48.txt','rt');
A = [];
xArr = [];
yArr = [];
filteredArray = [];
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
    y = c{2};
    %x = power(c{1}, 2) + power(c{2}, 2);
    t = c{5};

    xArr = [xArr, x];
    yArr = [yArr, y];
    tArr = [tArr, t];
    
end
filteredArray = ([0, 0, 0, 0, xArr] + 4*[0, 0, 0, xArr, 0] + 6*[0, 0, xArr, 0, 0] + 4*[0, xArr, 0, 0, 0] + 1*[xArr, 0, 0, 0, 0])/16;
filteredArray = filteredArray(3:end-2);

[peakvals, beatsArr] = findpeaks(filteredArray)
beatsTime = tArr(beatsArr)

figure(1);
%plot(tArr, xArr);
%hold on;
plot(tArr, filteredArray);
hold on;
plot(beatsTime, peakvals, '*');
%plot(tArr, yArr);
%plot(tArr, sqrt(xArr.^2 + yArr.^2));
%legend('x','y', 'parametric');
hold off;
%figure(2);
%plot(xArr, yArr);
%figure(3);

timediff = beatsTime(end -1) - beatsTime(end-2);
temp = diff(beatsTime);
timediff2 = mean(temp(end-5:end-1));

tempo = 1/(timediff/2/60000);
tempo2 = 1/(timediff2/2/60000);
disp(tempo);
disp(tempo2);
 % disp(A)
fclose(fid);
%you have now loaded all of the data.