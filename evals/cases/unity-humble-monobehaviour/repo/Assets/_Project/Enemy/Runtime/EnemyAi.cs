using UnityEngine;

public class EnemyAi : MonoBehaviour
{
    private EnemyPatrolRoute _patrol;

    void Awake()
    {
        _patrol = new EnemyPatrolRoute(transform);
    }

    void Update()
    {
        _patrol.Advance(Time.deltaTime);
    }
}
