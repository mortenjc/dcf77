




## Driving the ampere meters

The idea is to drive the ampere meters using pulse width modulation
(PWM) on the **esp32** to display hours, minutes, (seconds).

The esp32 gpio pins have an output voltage of either 3.3V when on and 0V when 
off. Bu we really need a (semi) continuous range between 0 and 3.3V.

We can achieve this by using PWM set to a resonable frequency and varying
the duty cycle.

One of my ammeters shows positive and negative currents. I need a voltage 
divider circuit that supports this.

![](images/voltage_divider.png)

Here r0 is the internal resistance of the ESP32 gpio pin(s) and ri is 
the internal resistance of the ammeter. These are fixed values and need 
to be measured.

Once these are known we need to calculate the value of R to achieve the
desired maximum current.

In my case r0 is 28 Ohms and ri is 13 Ohms.

Finally I measured the voltage over the two ammeter terminals (A, B) and 
discovered that the voltage was too high. To reduce it we added a capacitor.

