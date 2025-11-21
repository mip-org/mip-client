function kdtree_compile_cpp14()
% kdtree_compile_cpp14
% Build kdtree MEX files using MATLAB's own C++ compiler with -std=c++14
%
% This version avoids system GCC, avoids CXXFLAGS concatenation issues,
% and ensures ABI compatibility with MATLAB’s libstdc++.

    fprintf('--- kdtree MEX Build (C++14, MATLAB toolchain) ---\n');

    % Determine location of this script (kdtree/toolbox)
    localpath = fileparts(which('kdtree_compile'));
    fprintf('Building in: %s\n', localpath);

    %% Force MATLAB to use its own bundled GCC/G++
    mex -setup C++;  % Load MATLAB's default toolchain

    arch = computer('arch');
    matlab_gxx = fullfile(matlabroot, 'bin', arch, 'g++');
    matlab_gcc = fullfile(matlabroot, 'bin', arch, 'gcc');

    fprintf('MATLAB C++ compiler: %s\n', matlab_gxx);

    % Explicitly set CXX and CC inside MATLAB
    setenv('CXX', matlab_gxx);
    setenv('CC',  matlab_gcc);

    %% List of source files
    src_files = {
        'kdtree_build.cpp'
        'kdtree_delete.cpp'
        'kdtree_k_nearest_neighbors.cpp'
        'kdtree_ball_query.cpp'
        'kdtree_nearest_neighbor.cpp'
        'kdtree_range_query.cpp'
        'kdtree_io_from_mat.cpp'
        'kdtree_io_to_mat.cpp'
    };

    %% Build each MEX file
    err = 0;

    for k = 1:numel(src_files)
        src = fullfile(localpath, src_files{k});
        fprintf('\nCompiling %s...\n', src_files{k});

        % Use ONLY MATLAB's compiler + C++14 flag
        try
            mex('-v', ...
                ['CXX=' matlab_gxx], ...
                ['CC='  matlab_gcc], ...
                'CXXFLAGS=-std=c++14', ...
                '-outdir', localpath, ...
                src);
        catch ME
            warning("Error compiling %s:\n%s", src_files{k}, ME.message);
            err = 1;
        end
    end

    %% Check result
    if err
        error('One or more MEX files failed to compile.');
    else
        fprintf('\nAll kdtree MEX files compiled successfully.\n');
    end

    fprintf('--- Build complete ---\n');
end
