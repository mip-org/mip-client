function kdtree_compile_cpp14()
% Custom compilation script for kdtree with C++14 standard

localpath = fileparts(which('kdtree_compile'));
fprintf(1,'Compiling kdtree library [%s] with MATLAB toolchain and C++14...\n', localpath);

%% Force MATLAB to use its own C++ compiler
mex -setup C++;  % this loads MATLAB's default toolchain

% Get path to MATLAB's own GCC/G++
matlabroot_dir = matlabroot;
arch = computer('arch');
matlab_gxx = fullfile(matlabroot_dir, 'bin', arch, 'g++');
matlab_gcc = fullfile(matlabroot_dir, 'bin', arch, 'gcc');

% Override environment inside MATLAB
setenv('CXX', matlab_gxx);
setenv('CC',  matlab_gcc);

fprintf('Using MATLAB g++: %s\n', matlab_gxx);

%% C++14 flags + force linker to use same compiler
cxxflags = ['CXXFLAGS="$CXXFLAGS -std=c++14" ', ...
            'LD="$CXX" ', ...
            'LDXX="$CXX" '];

%% Build files
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

err = 0;
for k = 1:numel(src_files)
    src = fullfile(localpath, src_files{k});
    fprintf('Compiling %s...\n', src_files{k});
    err = err | mex(cxxflags, '-outdir', localpath, src);
end

if err ~= 0
   error('compile failed!');
else
   fprintf(1,'Done!\n');
end
