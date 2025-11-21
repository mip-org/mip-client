function import(packageName, varargin)
    % import - Import a mip package into MATLAB path
    %
    % Usage:
    %   mip.import('packageName')
    %
    % This function imports the specified package from ~/.mip/packages by
    % executing its setup.m file.
    
    % Parse optional arguments for internal use
    p = inputParser;
    addParameter(p, 'importingStack', {}, @iscell);
    parse(p, varargin{:});
    importingStack = p.Results.importingStack;
    
    % Check for circular dependencies
    if ismember(packageName, importingStack)
        cycle = strjoin([importingStack, {packageName}], ' -> ');
        error('mip:circularDependency', ...
              'Circular dependency detected: %s', cycle);
    end
    
    % Add to importing stack for circular dependency detection
    importingStack = [importingStack, {packageName}];
    
    % Get the mip packages directory
    homeDir = getenv('HOME');
    if isempty(homeDir)
        % Windows fallback
        homeDir = getenv('USERPROFILE');
    end
    
    packageDir = fullfile(homeDir, '.mip', 'packages', packageName);
    
    % Check if package exists
    if ~exist(packageDir, 'dir')
        error('mip:packageNotFound', ...
              'Package "%s" is not installed. Run "mip install %s" first.', ...
              packageName, packageName);
    end
    
    % Check if package is already imported
    if isPackageImported(packageName)
        fprintf('Package "%s" is already imported\n', packageName);
        return;
    end
    
    % Check for mip.json and process dependencies
    mipJsonPath = fullfile(packageDir, 'mip.json');
    if exist(mipJsonPath, 'file')
        try
            % Read and parse mip.json
            fid = fopen(mipJsonPath, 'r');
            jsonText = fread(fid, '*char')';
            fclose(fid);
            mipConfig = jsondecode(jsonText);
            
            % Import dependencies first
            if isfield(mipConfig, 'dependencies') && ~isempty(mipConfig.dependencies)
                fprintf('Importing dependencies for "%s": %s\n', ...
                        packageName, strjoin(mipConfig.dependencies, ', '));
                for i = 1:length(mipConfig.dependencies)
                    dep = mipConfig.dependencies{i};
                    if ~isPackageImported(dep)
                        mip.import(dep, 'importingStack', importingStack);
                    else
                        fprintf('  Dependency "%s" is already imported\n', dep);
                    end
                end
            end
        catch ME
            warning('mip:jsonParseError', ...
                    'Could not parse mip.json for package "%s": %s', ...
                    packageName, ME.message);
        end
    end
    
    % Look for setup.m file
    setupFile = fullfile(packageDir, 'setup.m');
    if ~exist(setupFile, 'file')
        error('mip:setupNotFound', ...
              'Package "%s" does not have a setup.m file', packageName);
    end
    
    % Execute the setup.m file
    originalDir = pwd;
    cd(packageDir);
    try
        run(setupFile);
        fprintf('Imported package "%s"\n', packageName);
    catch ME
        warning('mip:setupError', ...
                'Error executing setup.m for package "%s": %s', ...
                packageName, ME.message);
    end
    cd(originalDir);
    
    % Mark package as imported
    markPackageAsImported(packageName);
end

function imported = isPackageImported(packageName)
    % Helper function to check if a package has already been imported
    global MIP_IMPORTED_PACKAGES;
    if isempty(MIP_IMPORTED_PACKAGES)
        MIP_IMPORTED_PACKAGES = {};
    end
    imported = ismember(packageName, MIP_IMPORTED_PACKAGES);
end

function markPackageAsImported(packageName)
    % Helper function to mark a package as imported
    global MIP_IMPORTED_PACKAGES;
    if isempty(MIP_IMPORTED_PACKAGES)
        MIP_IMPORTED_PACKAGES = {};
    end
    if ~ismember(packageName, MIP_IMPORTED_PACKAGES)
        MIP_IMPORTED_PACKAGES{end+1} = packageName;
    end
end
