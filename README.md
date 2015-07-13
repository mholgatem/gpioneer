<h1>GPioneer - A Python Based GPIO Controller</h1>This is a GPIO controller that is fully compatible with Piplay (and RetroPie?). For anyone that is familiar with Adafruit's RetroGame Utility, this is very similar. The main difference being that this is user friendly and full featured.
<h4>What's New?</h4>
<ul><li>Configuration tool to auto map buttons to keystrokes</li>
<li>web-front end to easily modify settings/will auto integrate with piplay's web frontend</li>
<li>supports button combinations for additional keystrokes</li>
<li>map multiple keystrokes/commands to a single button</li>
<li><b>It supports system commands! (you can map volume/shutdown/etc to buttons)</b></li>
</ul>
<h4>How to install</h4>in terminal type:
<pre>cd ~
git clone https://github.com/mholgatem/gpioneer.git
bash gpioneer/install.sh</pre>
That's it! The installer is still very much in the beta stage, so let me know if you have problems. But I have tested it on several clean raspbian/piplay images with no problem.

<h4>How to use</h4>After the installer runs, you will be prompted to run the configuration tool. You will be prompted to press each direction twice to register the correct gpio pins (note: after registering 'up', you can skip any configuration by pressing up twice). 
After running the configuration, GPioneer will automatically run in the background. You can customize any buttons or add your own custom combos by going to the web interface on a local computer (Pi's ip address/if you have piplay installed, go to the 'database admin->GPioneer' section)

I'll be editing the 'readme' section of the git repository soon to add some extra info
