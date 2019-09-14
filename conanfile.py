from conans import ConanFile, CMake, tools, AutoToolsBuildEnvironment
from conans.tools import os_info, SystemPackageTool
import os
import shutil
import glob

class FFms2CoreConan(ConanFile):
    name = "ffms2-core"
    version = "2.31"
    description = "Keep it short"
    # topics can get used for searches, GitHub topics, Bintray tags etc. Add here keywords about the library
    topics = ("conan", "ffms2", "multimedia", "ffmpeg", "avisynth")
    url = "https://github.com/cqjjjzr/conan-ffms2"
    homepage = "https://github.com/FFMS/ffms2"
    author = "Charlie Jiang <cqjjjzr@gmail.com>"
    license = "MIT"  # Indicates license type of the packaged library; please use SPDX Identifiers https://spdx.org/licenses/
    exports = ["LICENSE.md"]      # Packages the license for the conanfile.py
    # Remove following lines if the target lib does not use cmake.
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"

    #not released
    git_commit = "a9e8f7397aeb341537743dea601cd7f7fe6b93ff"

    # Options may need to change depending on the packaged library.
    settings = "os", "arch", "compiler", "build_type"
    options = {"fPIC": [True, False]}
    default_options = {"fPIC": True}

    # Custom attributes for Bincrafters recipe conventions
    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "ffmpeg/4.2@charliejiang/stable"
    )

    @property
    def _is_mingw_windows(self):
        return self.settings.os == 'Windows' and self.settings.compiler == 'gcc' and os.name == 'nt'

    @property
    def _is_msvc(self):
        return self.settings.compiler == 'Visual Studio'

    def system_requirements(self):
        try:
            if (self._is_msvc):
                return
            if (os_info.detect_windows_subsystem() != None and os_info.detect_windows_subsystem() != 'WSL'):
                os.environ["CONAN_SYSREQUIRES_SUDO"] = "False"
            installer = SystemPackageTool()
            #installer.update()
            installer.install('autoconf')
            installer.install('automake')
            installer.install('libtool')
            installer.install('make')
            installer.install('pkg-config')
        except:
            self.output.warn('Unable to bootstrap required build tools.  If they are already installed, you can ignore this warning.')
            self.output.warn(traceback.print_exc())

    def build_requirements(self):
        if tools.os_info.is_windows:
            if "CONAN_BASH_PATH" not in os.environ:
                self.build_requires("msys2_installer/latest@bincrafters/stable")

    def _configure_cmake(self):
        cmake = CMake(self, set_cmake_flags=True)
        #cmake.definitions["CMAKE_VERBOSE_MAKEFILE"] = True
        cmake.configure(source_folder=self._source_subfolder,
                        build_folder=self._build_subfolder)
        return cmake

    def configure(self):
        del self.settings.compiler.libcxx

    def config_options(self):
        if self.settings.os == 'Windows' and self._is_msvc:
            del self.options.fPIC

    def source(self):
        source_url = "https://github.com/FFMS/ffms2"
        tools.get("{0}/archive/{1}.tar.gz".format(source_url, self.git_commit))
        extracted_dir = "ffms2-{0}".format(self.git_commit)
        # not released yet
        # but the latest release fails to build

        # Rename to "source_subfolder" is a convention to simplify later steps
        os.rename(extracted_dir, self._source_subfolder)

        shutil.copy("CMakeLists.txt", os.path.join(
            self._source_subfolder, "CMakeLists.txt"))
        tools.replace_in_file(os.path.join(self._source_subfolder, "configure.ac"), "AC_CONFIG_HEADERS([src/config/config.h])", "")
        tools.replace_in_file(os.path.join(self._source_subfolder, "Makefile.am"), "	@ZLIB_CPPFLAGS@ \\", "	@ZLIB_CPPFLAGS@")
        tools.replace_in_file(os.path.join(self._source_subfolder, "Makefile.am"), "	-include config.h", "")

    def _build_autotools(self):
        prefix = os.path.abspath(self.package_folder)
        host = None
        build = None
        if self._is_mingw_windows or self._is_msvc:
            prefix = prefix.replace('\\', '/')
            build = False
            if self.settings.arch == "x86":
                host = "i686-w64-mingw32"
            elif self.settings.arch == "x86_64":
                host = "x86_64-w64-mingw32"

        env_build = AutoToolsBuildEnvironment(self, win_bash=tools.os_info.is_windows)

        if self.settings.os != "Windows":
            env_build.fpic = self.options.fPIC

        configure_args = ['--prefix=%s' % prefix]
        configure_args.extend(['--enable-static', '--disable-shared'])

        env_vars = {
            "FFMPEG_LIBS": "-L%s" % self.deps_cpp_info["ffmpeg"].lib_paths[0],
            "FFMPEG_CFLAGS": "-I%s" % self.deps_cpp_info["ffmpeg"].include_paths[0]
        }

        with tools.chdir(self._source_subfolder):
            with tools.environment_append(env_vars):
                self.run("autoreconf -vfi", win_bash=tools.os_info.is_windows)
                env_build.configure(args=configure_args, host=host, build=build)
                env_build.make()
                env_build.install()

    def _build_cmake(self):
        shutil.copy("conanbuildinfo.cmake", os.path.join(
            self._source_subfolder, "conanbuildinfo.cmake"))
        cmake = self._configure_cmake()
        cmake.build()

    def build(self):
        if self._is_msvc:
            self._build_cmake()
        else:
            self._build_autotools()

    def package(self):
        self.copy(os.path.join(self._source_subfolder, "COPYING.LIB"),
                  dst="licenses", ignore_case=True, keep_path=False)
        if self._is_msvc:
            self.copy(pattern="*.dll", dst="bin", keep_path=False)
            cmake = self._configure_cmake()
            cmake.install()
        # remove libtool .la files - they have hard-coded paths
        if not self._is_msvc:
            with tools.chdir(os.path.join(self.package_folder, "lib")):
                for filename in glob.glob("*.la"):
                    os.unlink(filename)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
