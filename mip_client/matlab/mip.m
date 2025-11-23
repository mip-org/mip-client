function varargout = mip(command, varargin)
    % mip - MATLAB Interface for mip Package Manager
    %
    % Usage:
    %   mip import <package>       - Import a package into MATLAB path
    %   mip install <package>      - Install a package
    %   mip uninstall <package>    - Uninstall a package
    %   mip list                   - List installed packages
    %   mip setup                  - Set up MATLAB integration
    %   mip find-name-collisions   - Find symbol name collisions
    %
    % Examples:
    %   mip import mypackage
    %   mip install mypackage
    %   mip uninstall mypackage
    %   mip list
    
    if nargin < 1
        error('mip:noCommand', 'No command specified. Use "mip help" for usage information.');
    end
    
    % Handle 'import' command by calling mip.import
    if strcmp(command, 'import')
        if nargin < 2
            error('mip:noPackage', 'No package specified for import command.');
        end
        packageName = varargin{1};
        % Call mip.import with the package name and any additional arguments
        mip.import(packageName, varargin{2:end});
        return;
    end
    
    % For all other commands, forward to system call
    % Build the command string
    cmdStr = 'mip';
    cmdStr = [cmdStr, ' ', command];
    
    % Add all additional arguments
    for i = 1:length(varargin)
        arg = varargin{i};
        if ischar(arg) || isstring(arg)
            % Add quotes if argument contains spaces
            if contains(arg, ' ')
                cmdStr = [cmdStr, ' "', char(arg), '"'];
            else
                cmdStr = [cmdStr, ' ', char(arg)];
            end
        else
            error('mip:invalidArgument', 'All arguments must be strings or chars.');
        end
    end
    
    % Execute the system command
    [status, output] = system(cmdStr);
    
    % Display the output
    if ~isempty(output)
        fprintf('%s', output);
    end
    
    % Check for errors
    if status ~= 0
        error('mip:commandFailed', 'Command failed with status %d', status);
    end
    
    % Return output if requested
    if nargout > 0
        varargout{1} = output;
    end
end
