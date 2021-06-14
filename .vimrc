
" :echo v:version
" https://stackoverflow.com/questions/9193066/how-do-i-inspect-vim-variables

" https://github.com/junegunn/vim-plug/wiki/tips
" https://github.com/junegunn/vim-plug/issues/894
if v:version >= 740

  if empty(glob('~/.vim/autoload/plug.vim'))
    let s:downloadurl = "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim"
    let s:destinedirectory = $HOME . "/.vim/autoload"
    let s:destinefile = s:destinedirectory . "/plug.vim"

    if !isdirectory(s:destinedirectory)
      call mkdir(s:destinedirectory, "p")
    endif

    if executable("curl")
      silent execute '!curl --output ' . s:destinefile .
          \ ' --create-dirs --location --fail --silent ' . s:downloadurl

    else
      silent execute '!wget --output-document ' . s:destinefile .
          \ ' --no-host-directories --force-directories --quiet ' . s:downloadurl
    endif

  endif

  if !empty(glob('~/.vim/autoload/plug.vim'))
    " https://github.com/junegunn/vim-plug/issues/896
    let g:plug_home = $HOME . '/.vim/plugged'

    if has('win32unix')
    \ && executable('cygpath')
    \ && executable('git')
    \ && split(system('git --version'))[2] =~# 'windows'
      " Use mixed path on Cygwin so that Windows git works
      let g:plug_home = substitute(system('cygpath -m ' . g:plug_home), '\r*\n\+$', '', '')
    endif

    " https://github.com/junegunn/vim-plug
    call plug#begin()

    " Run PlugInstall if there are missing plugins
    " https://github.com/junegunn/vim-plug/issues/1018
    if len(filter(values(g:plugs), '!isdirectory(v:val.dir)'))
      autocmd VimEnter * PlugInstall --sync | source $MYVIMRC
    endif

    if v:version >= 800
      let s:pythonexecutable = "notinstalled"

      if executable("python")
        let s:pythonexecutable = "python"
      endif

      if executable("python3")
        let s:pythonexecutable = "python3"
      endif

      " https://vi.stackexchange.com/questions/9606/vim-compiled-with-python3-but-haspython-returns-0
      if s:pythonexecutable != 'notinstalled'

        let s:ispython3supported = system( s:pythonexecutable .
            \ ' -c "import sys; sys.stdout.write(
            \    str( int( sys.version_info[0] > 2 and sys.version_info[1] > 5 ) )
            \    )"' )

        if s:ispython3supported == '1' && has('python3')

          if has('nvim')
            Plug 'Shougo/deoplete.nvim', { 'do': ':UpdateRemotePlugins' }

          else
            Plug 'Shougo/deoplete.nvim'
            Plug 'roxma/nvim-yarp'
            Plug 'roxma/vim-hug-neovim-rpc'

          endif

        endif

      endif

    endif

    " Initialize plugin system
    call plug#end()

  endif

endif

" https://stackoverflow.com/questions/42298671/libpython2-7-dll-a-in-cygwin
" https://stackoverflow.com/questions/34309101/vim-could-not-load-library-libpython
" https://vi.stackexchange.com/questions/18222/compiling-vim-with-python3-showing-e370-could-not-load-library-libpython3-7m-a
" https://github.com/vim/vim-win32-installer/issues/48
if has('win32unix')
  if executable("python3.6")
    let g:python3_host_prog = 'python3.6'
    let &pythonthreedll = 'libpython3.6m.dll'
  endif
endif

" Start deoplete when available
let g:deoplete#enable_at_startup = 1


" https://superuser.com/questions/401926/how-to-get-shiftarrows-and-ctrlarrows-working-in-vim-in-tmux
if &term =~ '^screen'
    " tmux will send xterm-style keys when its xterm-keys option is on
    execute "set <xUp>=\e[1;*A"
    execute "set <xDown>=\e[1;*B"
    execute "set <xRight>=\e[1;*C"
    execute "set <xLeft>=\e[1;*D"
endif

" https://vi.stackexchange.com/questions/2223/how-to-tell-vim-not-to-try-to-unzip-a-file
" let g:loaded_zipPlugin = 1
" let g:loaded_zip       = 1

set history=10000         " remember more commands and search history

" Color Themes
:colorscheme elflord

" http://vimdoc.sourceforge.net/htmldoc/change.html#registers
" https://stackoverflow.com/questions/9166328/how-to-copy-selected-lines-to-clipboard-in-vim
" breaks yank on Windows on Windows least, use " * y or " + y  to copy things to system clipboard instead
" set clipboard=unnamedplus

set formatoptions-=t

" Best view with a 256 color terminal and Powerline fonts
if has('autocmd')
  filetype plugin indent on
  " Uncomment the following to have Vim jump to the last position when reopening a file
  au BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal! g'\"" | endif
endif

" Enable syntax highlighting
syntax on

if has('syntax') && !exists('g:syntax_on')
  syntax enable
endif

" https://stackoverflow.com/questions/55050366/how-to-set-vim-highlight-colorcolumn-guideline-transparency
highlight ColorColumn ctermbg=238

" https://vim.fandom.com/wiki/Automatic_word_wrapping
" https://stackoverflow.com/questions/2447109/showing-a-different-background-colour-in-vim-past-80-characters
if v:version >= 730
  set colorcolumn=100
endif

" https://vim.fandom.com/wiki/Automatic_word_wrapping
set tw=0

" https://vim.fandom.com/wiki/Make_search_results_appear_in_the_middle_of_the_screen
" https://vi.stackexchange.com/questions/7699/how-do-i-make-vim-always-display-several-lines-after-eof
set scrolloff=10

" URL: http://vim.wikia.com/wiki/Example_vimrc
" Authors: http://vim.wikia.com/wiki/Vim_on_Freenode
" Description: A minimal, but feature rich, example .vimrc. If you are a
"              newbie, basing your first .vimrc on this file is a good choice.
"              If you're a more advanced user, building your own .vimrc based
"              on this file is still a good idea.

"------------------------------------------------------------
" Features {{{1
"
" These options and commands enable some very useful features in Vim, that
" no user should have to live without.

" Set 'nocompatible' to ward off unexpected things that your distro might
" have made, as well as sanely reset options when re-sourcing .vimrc
set nocompatible

" Attempt to determine the type of a file based on its name and possibly its
" contents. Use this to allow intelligent auto-indenting for each filetype,
" and for plugins that are filetype specific.
filetype indent plugin on

" filetype off



"------------------------------------------------------------
" Must have options {{{1
"
" These are highly recommended options.

" Vim with default settings does not allow easy switching between multiple files
" in the same editor window. Users can use multiple split windows or multiple
" tab pages to edit multiple files, but it is still best to enable an option to
" allow easier switching between files.
"
" One such option is the 'hidden' option, which allows you to re-use the same
" window and switch from an unsaved buffer without saving it first. Also allows
" you to keep an undo history for multiple files when re-using the same window
" in this way. Note that using persistent undo also lets you undo in multiple
" files even in the same window, but is less efficient and is actually designed
" for keeping undo history after closing Vim entirely. Vim will complain if you
" try to quit without saving, and swap files will keep you safe if your computer
" crashes.
"
" do not history when leavy buffer
set hidden

" Note that not everyone likes working this way (with the hidden option).
" Alternatives include using tabs or split windows instead of re-using the same
" window as mentioned above, and/or either of the following options:
" set autowriteall

" Instead of failing a command because of unsaved changes, instead raise a
" dialogue asking if you wish to save changed files.
set confirm

" Better command-line completion
set wildmenu

" Show partial commands in the last line of the screen
set showcmd

" Highlight searches (use <C-L> to temporarily turn off highlighting;
" See the mapping of <C-L> below)
set hlsearch

" Modelines have historically been a source of security vulnerabilities. As
" such, it may be a good idea to disable them and use the securemodelines
" script, <http://www.vim.org/scripts/script.php?script_id=1876>.
" set nomodeline


"------------------------------------------------------------
" Usability options {{{1
"
" These are options that users frequently set in their .vimrc. Some of them
" change Vim's behaviour in ways which deviate from the true Vi way, but
" which are considered to add usability. Which, if any, of these options to
" use is very much a personal preference, but they are harmless.

" Use case insensitive search, except when using capital letters
set ignorecase
set smartcase

" Allow backspacing over autoindent, line breaks and start of insert action
set backspace=indent,eol,start

" When opening a new line and no filetype-specific indenting is enabled, keep
" the same indent as the line you're currently on. Useful for READMEs, etc.
set autoindent

" Stop certain movements from always going to the first character of a line.
" While this behaviour deviates from that of Vi, it does what most users
" coming from other editors would expect.
set nostartofline

" Always display the status line, even if only one window is displayed
set laststatus=1

" Use visual bell instead of beeping when doing something wrong
set visualbell

" And reset the terminal code for the visual bell. If visualbell is set, and
" this line is also included, vim will neither flash nor beep. If visualbell
" is unset, this does nothing.
set t_vb=

" Set the command window height to 2 lines, to avoid many cases of having to
" "press <Enter> to continue"
" https://stackoverflow.com/questions/55053173/why-setting-the-command-window-height-to-2-lines
set cmdheight=1

" Display line numbers on the left
set number

" Quickly time out on keycodes, but never time out on mappings
set notimeout ttimeout ttimeoutlen=200

" Use <F11> to toggle between 'paste' and 'nopaste'
" https://stackoverflow.com/questions/2514445/turning-off-auto-indent-when-pasting-text-into-vim
set paste
set pastetoggle=<F11>



"------------------------------------------------------------
" Indentation options {{{1
"
" Indentation settings according to personal preference.
"
" Indentation settings for using 2 spaces instead of tabs.
" Do not change 'tabstop' from its default value of 8 with this setup.
set shiftwidth=4
set softtabstop=4
set expandtab

" Indentation settings for using hard tabs for indent. Display tabs as
" two characters wide.
set tabstop=4



" vim-sublime - A minimal Sublime Text -like vim experience bundle
"               http://github.com/grigio/vim-sublime
"
" Use :help 'option' to see the documentation for the given option.
set complete-=i
set showmatch
set showmode
set smarttab

set nrformats-=octal
set shiftround
set incsearch
set autoread
set encoding=utf-8

"set listchars=tab:▒░,trail:▓
set nolist

" Enable use of the mouse for all modes
" In many terminal emulators the mouse works just fine, thus enable it.
if has('mouse')
  " Fix scroll inside tmux. Use `:help 'mouse'` inside vim for help about `mouse=a` vs `mouse=v`
  " https://superuser.com/questions/610114/tmux-enable-mouse-scrolling-in-vim-instead-of-history-buffer
  set mouse=a
endif

set nobackup
set nowritebackup
set noswapfile
set fileformats=unix,dos,mac
set completeopt=menuone,longest,preview

" Display the cursor position on the last line of the screen or in the status
" line of a window https://vi.stackexchange.com/questions/13539/why-does-set-ruler-get-reset-to-noruler
set ruler


"
" Plugins config
"

" CtrlP
set wildignore+=*/.git/*,*/.hg/*,*/.svn/*

" Ultisnip
" NOTE: <f1> otherwise it overrides <tab> forever
let g:UltiSnipsExpandTrigger="<f1>"
let g:UltiSnipsJumpForwardTrigger="<f1>"
let g:UltiSnipsJumpBackwardTrigger="<c-k>"
let g:did_UltiSnips_vim_after = 1

" vim-airline
let g:airline#extensions#tabline#enabled = 1
let g:airline_powerline_fonts = 1

" Disable tComment to escape some entities
let g:tcomment#replacements_xml={}


" Tabs
let g:airline_theme='badwolf'
let g:airline#extensions#tabline#enabled = 1



"------------------------------------------------------------
" Mappings {{{1
"
" Useful mappings
"
" Map Y to act like D and C, i.e. to yank until EOL, rather than act as yy,
" which is the default
"map Y y$

map <C-a> <esc>ggVG<CR>

" Don't use Ex mode, use Q for formatting
map Q gq

"
" Basic shortcuts definitions
"  most in visual mode / selection (v or ⇧ v)
"
" Find
map <C-f> /

" comment / decomment & normal comment behavior
vmap <C-m> gc

" Text wrap simpler, then type the open tag or ',"
vmap <C-w> S
set wrap

" Cut, Paste, Copy
vmap <C-x> d
vmap <C-v> p
vmap <C-c> y

inoremap <C-U> <C-G>u<C-U>

" exit insert mode
inoremap <C-c> <Esc>

" indend / deindent after selecting the text with (⇧ v), (.) to repeat.
vnoremap <Tab> >
vnoremap <S-Tab> <

" " FIXME: (broken) ctrl s to save
" noremap  <C-S> :update<CR>
" vnoremap <C-S> <C-C>:update<CR>
" inoremap <C-S> <Esc>:update<CR>

" " Undo, Redo (broken)
" nnoremap <C-z>  :undo<CR>
" inoremap <C-z>  <Esc>:undo<CR>
" nnoremap <C-y>  :redo<CR>
" inoremap <C-y>  <Esc>:redo<CR>

" Use <C-L> to clear the highlighting of :set hlsearch.
if maparg('<C-L>', 'n') ==# ''
  nnoremap <silent> <C-L> :nohlsearch<CR><C-L>
endif

" Map <C-L> (redraw screen) to also turn off search highlighting until the
" next search
nnoremap <C-L> :nohl<CR><C-L>

nnoremap <C-b>  :tabprevious<CR>
inoremap <C-b>  <Esc>:tabprevious<CR>i
nnoremap <C-n>  :tabnext<CR>

"inoremap <C-n>  <Esc>:tabnext<CR>i
"nnoremap <C-t>  :tabnew<CR>

inoremap <C-t>  <Esc>:tabnew<CR>i
nnoremap <C-k>  :tabclose<CR>
inoremap <C-k>  <Esc>:tabclose<CR>i

nnoremap mj :m .+1<CR>==
nnoremap mk :m .-2<CR>==

nnoremap th  :tabfirst<CR>
nnoremap tj  :tabnext<CR>
nnoremap tk  :tabprev<CR>
nnoremap tl  :tablast<CR>
nnoremap tt  :tabedit<Space>
nnoremap tn  :tabnext<Space>
nnoremap tm  :tabm<Space>
nnoremap td  :tabclose<CR>

" Alternatively use
"nnoremap th :tabnext<CR>
"nnoremap tl :tabprev<CR>
"nnoremap tn :tabnew<CR>


" lazy ':'
map \ :

let mapleader = ','
nnoremap <Leader>p :set paste<CR>
nnoremap <Leader>o :set nopaste<CR>
noremap  <Leader>g :GitGutterToggle<CR>

" this machine config
if filereadable(expand("~/.vimrc.local"))
  source ~/.vimrc.local
endif
