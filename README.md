<h1>GPioneer</h1>
<h6>A Python Based GPIO Controller</h6>This is a GPIO controller that is fully compatible with Piplay (and RetroPie?). For anyone that is familiar with Adafruit's RetroGame Utility, this is very similar. The main difference being that this is user friendly and full featured.
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

<h4>How to use</h4> After the installer runs, you will be prompted to run the configuration tool. You will be prompted to press each direction twice to register the correct gpio pins (note: after registering 'up', you can skip any configuration by pressing up twice). 
After running the configuration, GPioneer will automatically run in the background. You can customize any buttons or add your own custom combos by going to the web interface on a local computer (Pi's ip address/if you have piplay installed, go to the 'database admin->GPioneer' section)

<h4>Advanced configuration</h4>
/etc/rc.local has been modified to auto run GPioneer, add any of these flags to modify the runtime settings

<h6>Optional Flags</h6><ul><li>--combo_time	'Time in milliseconds to wait for combo buttons'</li>
<li>--key_repeat	'Delay in milliseconds before key repeat'</li>
<li>--key_delay	'Delay in milliseconds between key presses'</li>
<li>--pins		'Comma delimited pin numbers to watch'</li>
<li>--use_bcm		'use bcm numbering instead of board pin'</li>
<li>--debounce	'Time in milliseconds for button debounce'</li>
<li>--pulldown	'Use PullDown resistors instead of PullUp'</li>
<li>--poll_rate	'Rate to poll pins after IRQ detect'</li></ul>

<h6>Configuration Flags</h6><ul><li>-c				'Configure GPioneer'</li>
<li>--configure		'Configure GPioneer'</li>
<li>--button_count	'Number of player buttons to configure'</li></ul>
