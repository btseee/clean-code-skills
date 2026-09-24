using UnityEngine;

public class PlayerHealth : MonoBehaviour
{
    public int maxHealth = 100;
    public int currentHealth = 100;
    public float regenPerSecond = 1f;

    void Update()
    {
        if (currentHealth < maxHealth)
        {
            currentHealth += Mathf.RoundToInt(regenPerSecond * Time.deltaTime);
            if (currentHealth > maxHealth)
            {
                currentHealth = maxHealth;
            }
        }
    }

    public void TakeDamage(int amount)
    {
        currentHealth -= amount;
        if (currentHealth < 0)
        {
            currentHealth = 0;
        }
    }
}
