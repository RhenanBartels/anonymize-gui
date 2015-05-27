function anonymizegui()

    %Get the user`s screen size to help centering the interface
    screenSize = get(0,'ScreenSize');

    %Main window
    mainFigure = figure('Tag',mfilename,...
        'MenuBar','None',...        
        'IntegerHandle','off',...
        'Units', 'Normalized',...
        'Resize','on',...
        'NumberTitle','off',...
        'Name',sprintf('Anonymization Tool'),...
        'Visible','on',...
        'Position',[screenSize(1) / 2 - 0.2, screenSize(2) / 2 - 0.1, 0.4, 0.15] ,... %400,50,1050,700
        'Tag','mainfig');
    
    figureBackGroundColor = get(mainFigure, 'Color');
    
    folderLabel = uicontrol('Parent', mainFigure,...
        'String', 'Folder:',...
        'Style', 'Text',...
        'FontWeight', 'Bold',...
        'Units', 'Normalized',...
        'Backgroundcolor', figureBackGroundColor,...
        'Position', [0.01, 0.8, 0.1, 0.12]);
    
    folderEdit = uicontrol('Parent', mainFigure,...
        'Style', 'Edit',...
        'Backgroundcolor', [1 1 1],...
        'Units', 'Normalized',...
        'Position', [0.12, 0.73, 0.87, 0.25],...
        'Enable', 'Inactive',...
        'Tag', 'folderEdit');
    
    loadButton = uicontrol('Parent',mainFigure,...
        'Units', 'Normalized',...
        'Position', [0.35, 0.25, 0.15, 0.25],...
        'String', 'Load',...
        'Callback', @loadFolder);
    
    runButton = uicontrol('Parent',mainFigure,...
        'Units', 'Normalized',...
        'Position', [0.55, 0.25, 0.15, 0.25],...
        'String', 'Run',...
        'Tag', 'runButton',...
        'Enable', 'Off',...
        'Callback', @runCallback);
    
    handles.graph = guihandles(mainFigure);
    guidata(mainFigure, handles)
    
                          
end


function loadFolder(hObject, eventdata)
 
    handles = guidata(hObject);    
    filesFolder = uigetdir('Select a folder');
    
    if filesFolder
        set(handles.graph.folderEdit, 'String', filesFolder);
        set(handles.graph.runButton, 'Enable', 'On');
        handles.data.filesFolder = filesFolder;
        guidata(hObject, handles);
    end

end

function runCallback(hObject, eventdata)  
    import java.util.UUID
    handles = guidata(hObject);
    filesFolder = handles.data.filesFolder;
    listFiles = dir(filesFolder);
    
    nFiles =length(listFiles);
    newFolderDicoms = [filesFolder filesep 'AnonymizedDicoms'];
    newFolderPatients = [filesFolder filesep 'AnonymizedPatientFiles'];
    createFolder(newFolderDicoms)
    createFolder(newFolderPatients)
    dicomsFolder = [filesFolder filesep 'AnonymizedDicoms'];
    patientFolder = [filesFolder filesep 'AnonymizedPatientFiles'];

    w = waitbar(0, 'Anonymizing...');
    for file = 1:nFiles

        dicomNames = {};
        currentName = listFiles(file).name;
        if listFiles(file).isdir && ~strcmp(currentName, '.') &&...
                ~strcmp(currentName, '..') &&...
                ~strcmp(currentName, '.DS_Store') &&...
                ~strcmp(currentName, '.git')
            
            newID = char(UUID.randomUUID());
            newID = newID(1:8);            
            dicomFolderName = dateFolderName(newID);
            finalDicomFolder = [newFolderDicoms filesep dicomFolderName];
            finalPatientFileName = [newFolderPatients filesep...
                dicomFolderName];
            createFolder(finalDicomFolder);
            
            %Get the DICOMs in the patient` root folder.
            dicomNames = hasDicom(filesFolder, currentName, dicomNames);
            %Go down one more folder
            subFolders = dir([filesFolder filesep currentName]);
            dicomNames = walkSubFolder(filesFolder, currentName, subFolders, dicomNames);
            if ~isempty(dicomNames)
                dicomPos = 1;
                for dicom = dicomNames                    
                    anonymize(dicom, newID, finalDicomFolder, dicomPos,...
                        finalPatientFileName);
                    dicomPos = dicomPos + 1;
                end
            end
        end
        
        waitbar(file / nFiles);
        
    end
    close(w)
    
end

function ends = endswith(fileName, suffix)
n = length(suffix);

ends = strcmp(fileName(end - n + 1:end), suffix);
end

function dicomNames = hasDicom(folderPath, folderName, dicomNames)
fullPath = [folderPath filesep folderName];
listFiles = dir(fullPath);
nFiles = length(listFiles);


for file = 1:nFiles
    if ~listFiles(file).isdir
        if endswith(listFiles(file).name, '.dcm')
            dicomNames{end + 1} = [fullPath filesep listFiles(file).name];
        end
    end
end

end

function dicomNames = walkSubFolder(rootPath, parentFolder, listFolder, dicomNames)
nFiles = length(listFolder);
fullPath = [rootPath filesep parentFolder];
for file = 1:nFiles
    currentName = listFolder(file).name;
    if listFolder(file).isdir && ~strcmp(currentName, '.') &&...
            ~strcmp(currentName, '..') &&...
            ~strcmp(currentName, '.DS_Store') &&...
            ~strcmp(currentName, '.git')
            
            dicomNames = hasDicom(fullPath, currentName, dicomNames);
            
        
    end
end

end

function dateFolder = dateFolderName(newID)
today = clock();
year = num2str(today(1));
month = num2str(today(2));
day = num2str(today(3));
if length(month) < 2
    month = ['0' month];
end
if length(day) < 2
    day = ['0' day];
end
    
   dateFolder = [year month day '_' newID];

end

function createFolder(newFolder)    
    s = mkdir(newFolder);  
end

function anonymize(dicomFile, newID, outputPath, dicomPos, patientFolder)
    
    outputFileName = [patientFolder '.txt'];
    
    fieldTagsGroup = {'8', '10', '20'};
    fieldTags = {'20', '80', '81', '90', '20', '10', '30'};
    
    secret = '********************';
    metadata = dicominfo(dicomFile{1});
    studyDate = dicomlookup(fieldTagsGroup{1}, fieldTags{1});
    instName = dicomlookup(fieldTagsGroup{1}, fieldTags{2});
    instAddress = dicomlookup(fieldTagsGroup{1}, fieldTags{3});
    physName = dicomlookup(fieldTagsGroup{1}, fieldTags{4});
    studyID = dicomlookup(fieldTagsGroup{2}, fieldTags{5});
    patID = dicomlookup(fieldTagsGroup{3}, fieldTags{6});
    patName = dicomlookup(fieldTagsGroup{2}, fieldTags{6});
    birthday = dicomlookup(fieldTagsGroup{2}, fieldTags{7});
    
    try
        sliceLocation = num2str(metadata.SliceLocation);
        sliceLocation = regexprep(sliceLocation, '\-', '');
        sliceLocation = regexprep(sliceLocation, '\.', '');
    catch
        sliceLocation = num2str(dicomPos);
    end
    
    %Create the patient file
    fobj = fopen(outputFileName, 'w');
    fprintf(fobj, ['StudyDate -> ' metadata.(studyDate) '\r\n']);
    fprintf(fobj, ['InstitutionName ->' metadata.(instName) '\r\n']);
    fprintf(fobj, ['instAddress -> ' metadata.(instAddress) '\r\n']);
    fprintf(fobj, ['PhysicianName -> ' metadata.(physName).FamilyName  '\r\n']);
    fprintf(fobj, ['StudyId -> ' metadata.(studyID) '\r\n']);
    fprintf(fobj, ['PatientId-> ' newID '\r\n']);
    fprintf(fobj, ['PatientName -> ' metadata.(patName).FamilyName '\r\n']);
    fprintf(fobj, ['Birthday -> ' metadata.(birthday) '\r\n']);
    fclose(fobj);
    
    metadata.(studyDate) = secret;
    metadata.(instName) = secret;
    metadata.(instAddress) = secret;
    metadata.(physName) = secret;
    metadata.(studyID) = newID;
    metadata.(patID) = secret;
    metadata.(patName) = secret;
    metadata.(birthday) = secret;
    
    finalPath = [outputPath filesep sliceLocation '.dcm'];
    dicomObj = dicomread(dicomFile{1});
    dicomwrite(dicomObj, finalPath, metadata);
    

    
    
end